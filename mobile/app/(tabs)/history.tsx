import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import { router, useFocusEffect } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { API_BASE } from '../../config';

interface Journal {
  id: number;
  url: string;
  name: string;
  crawled_at: string;
}

interface Paper {
  id: number;
  title: string;
  authors: string[];
  abstract: string;
  paper_url: string;
  doi: string;
  published_date: string;
}

export default function HistoryScreen() {
  const [journals, setJournals] = useState<Journal[]>([]);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const [jr, pr] = await Promise.all([
        fetch(`${API_BASE}/api/journals`).then((r) => r.json()),
        fetch(`${API_BASE}/api/papers?limit=50`).then((r) => r.json()),
      ]);
      setJournals(jr.journals || []);
      setPapers(pr.papers || []);
    } catch (e) {
      // 静默失败
    } finally {
      setLoading(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      loadData();
    }, [])
  );

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const openPaper = (paper: Paper) => {
    router.push(`/paper/${paper.id}`);
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#2563EB" />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>📚 历史记录</Text>
        <Text style={styles.headerSub}>
          已爬取 {journals.length} 个期刊，共保存论文
        </Text>
      </View>

      {/* Journal list */}
      {journals.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>期刊列表</Text>
          {journals.slice(0, 5).map((j) => (
            <View key={j.id} style={styles.journalItem}>
              <Text style={styles.journalUrl} numberOfLines={1}>
                {j.url}
              </Text>
              <Text style={styles.journalDate}>{j.crawled_at}</Text>
            </View>
          ))}
        </>
      )}

      {/* Paper list */}
      <Text style={styles.sectionTitle}>最近论文</Text>
      <FlatList
        data={papers}
        keyExtractor={(item, idx) => item.id?.toString() || String(idx)}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.paperItem}
            onPress={() => openPaper(item)}
            activeOpacity={0.7}
          >
            <Text style={styles.paperTitle} numberOfLines={2}>
              {item.title}
            </Text>
            <Text style={styles.paperAuthors} numberOfLines={1}>
              {item.authors.slice(0, 3).join(', ')}
            </Text>
          </TouchableOpacity>
        )}
        style={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor="#2563EB" />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>暂无记录</Text>
            <Text style={styles.emptyHint}>去"爬取"页面输入链接开始使用</Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
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
  sectionTitle: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 8,
    fontSize: 15,
    fontWeight: '600',
    color: '#475569',
  },
  journalItem: {
    marginHorizontal: 20,
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    padding: 12,
    marginBottom: 6,
    borderWidth: 1,
    borderColor: '#F1F5F9',
  },
  journalUrl: {
    fontSize: 13,
    color: '#2563EB',
  },
  journalDate: {
    fontSize: 11,
    color: '#94A3B8',
    marginTop: 4,
  },
  list: {
    paddingHorizontal: 20,
    paddingBottom: 30,
  },
  paperItem: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    padding: 14,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#F1F5F9',
  },
  paperTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1E293B',
    lineHeight: 21,
  },
  paperAuthors: {
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 4,
  },
  empty: {
    alignItems: 'center',
    paddingTop: 60,
  },
  emptyText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#64748B',
  },
  emptyHint: {
    fontSize: 13,
    color: '#94A3B8',
    marginTop: 6,
  },
});
