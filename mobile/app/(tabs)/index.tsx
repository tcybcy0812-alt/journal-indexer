import { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  RefreshControl,
} from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { API_BASE } from '../../config';
import PaperCard from '../../components/PaperCard';

interface Paper {
  id: number;
  title: string;
  authors: string[];
  abstract: string;
  paper_url: string;
  doi: string;
  published_date: string;
}

export default function HomeScreen() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const handleCrawl = async () => {
    if (!url.trim()) {
      setError('请输入期刊链接');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/crawl`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() }),
      });
      const data = await resp.json();
      if (data.success) {
        setPapers(data.papers);
      } else {
        setError(data.error || '爬取失败，请检查链接');
        setPapers([]);
      }
    } catch (e: any) {
      setError(`网络错误: ${e.message}\n请确认电脑后端已启动且 IP 配置正确`);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const resp = await fetch(`${API_BASE}/api/papers?limit=50`);
      const data = await resp.json();
      setPapers(data.papers);
    } catch (e) {
      // 静默失败
    } finally {
      setRefreshing(false);
    }
  };

  const openDetail = (paper: Paper) => {
    router.push(`/paper/${paper.id}`);
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>📖 期刊论文索引</Text>
          <Text style={styles.headerSub}>输入期刊目录链接，一键爬取论文</Text>
        </View>

        {/* Input Area */}
        <View style={styles.inputArea}>
          <TextInput
            style={styles.input}
            placeholder="粘贴期刊链接，如 https://arxiv.org/list/cs.AI/recent"
            placeholderTextColor="#9CA3AF"
            value={url}
            onChangeText={setUrl}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
            returnKeyType="go"
            onSubmitEditing={handleCrawl}
            editable={!loading}
          />
          <TouchableOpacity
            style={[styles.crawlBtn, loading && styles.crawlBtnDisabled]}
            onPress={handleCrawl}
            disabled={loading}
            activeOpacity={0.8}
          >
            {loading ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Text style={styles.crawlBtnText}>开始爬取</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Error */}
        {error ? (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        ) : null}

        {/* Paper List */}
        {papers.length > 0 && (
          <View style={styles.resultHeader}>
            <Text style={styles.resultTitle}>找到 {papers.length} 篇论文</Text>
          </View>
        )}

        <FlatList
          data={papers}
          keyExtractor={(item, idx) => item.id?.toString() || String(idx)}
          renderItem={({ item }) => (
            <PaperCard paper={item} onPress={() => openDetail(item)} />
          )}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor="#2563EB" />
          }
          ListEmptyComponent={
            !loading && !error ? (
              <View style={styles.empty}>
                <Text style={styles.emptyIcon}>🔍</Text>
                <Text style={styles.emptyText}>输入期刊链接开始爬取</Text>
                <Text style={styles.emptyHint}>支持 arXiv、Nature、Science 等期刊网站</Text>
              </View>
            ) : null
          }
        />
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 8,
  },
  headerTitle: {
    fontSize: 26,
    fontWeight: '700',
    color: '#1E293B',
  },
  headerSub: {
    fontSize: 14,
    color: '#64748B',
    marginTop: 4,
  },
  inputArea: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    gap: 10,
  },
  input: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 15,
    color: '#1E293B',
  },
  crawlBtn: {
    backgroundColor: '#2563EB',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
    height: 50,
  },
  crawlBtnDisabled: {
    backgroundColor: '#93C5FD',
  },
  crawlBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  errorBox: {
    marginHorizontal: 20,
    backgroundColor: '#FEF2F2',
    borderRadius: 10,
    padding: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#EF4444',
  },
  errorText: {
    color: '#991B1B',
    fontSize: 14,
    lineHeight: 20,
  },
  resultHeader: {
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 4,
  },
  resultTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#475569',
  },
  list: {
    paddingHorizontal: 20,
    paddingBottom: 30,
  },
  empty: {
    alignItems: 'center',
    paddingTop: 80,
  },
  emptyIcon: {
    fontSize: 48,
  },
  emptyText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#64748B',
    marginTop: 12,
  },
  emptyHint: {
    fontSize: 13,
    color: '#94A3B8',
    marginTop: 6,
  },
});
