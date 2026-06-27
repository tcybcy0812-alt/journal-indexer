import { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  Linking,
  Share,
} from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { API_BASE } from '../../config';

interface Paper {
  id: number;
  title: string;
  authors: string[];
  abstract: string;
  paper_url: string;
  doi: string;
  published_date: string;
  crawled_at: string;
  journal_url: string;
}

export default function PaperDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [paper, setPaper] = useState<Paper | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPaper();
  }, [id]);

  const loadPaper = async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/papers/${id}`);
      if (resp.ok) {
        setPaper(await resp.json());
      }
    } catch (e) {
      // 静默失败
    } finally {
      setLoading(false);
    }
  };

  const openLink = (url: string) => {
    if (url) Linking.openURL(url);
  };

  const handleShare = async () => {
    if (!paper) return;
    try {
      await Share.share({
        message: `${paper.title}\n作者: ${paper.authors.join(', ')}\n${paper.doi ? 'DOI: ' + paper.doi + '\n' : ''}${paper.paper_url}`,
      });
    } catch (e) {
      // 忽略
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator size="large" color="#2563EB" />
      </SafeAreaView>
    );
  }

  if (!paper) {
    return (
      <SafeAreaView style={styles.center}>
        <Text style={styles.errorText}>论文不存在或已被删除</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
        {/* Title */}
        <Text style={styles.title}>{paper.title}</Text>

        {/* Authors */}
        <View style={styles.authorsSection}>
          <Text style={styles.label}>👤 作者</Text>
          <View style={styles.authorList}>
            {paper.authors.map((author, idx) => (
              <View key={idx} style={styles.authorBadge}>
                <Text style={styles.authorText}>{author}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Abstract */}
        {paper.abstract ? (
          <View style={styles.section}>
            <Text style={styles.label}>📝 摘要</Text>
            <Text style={styles.abstract}>{paper.abstract}</Text>
          </View>
        ) : null}

        {/* Meta info */}
        <View style={styles.section}>
          <Text style={styles.label}>ℹ️ 信息</Text>
          <View style={styles.metaGrid}>
            {paper.doi ? (
              <View style={styles.metaItem}>
                <Text style={styles.metaKey}>DOI</Text>
                <Text style={styles.metaValue}>{paper.doi}</Text>
              </View>
            ) : null}
            {paper.published_date ? (
              <View style={styles.metaItem}>
                <Text style={styles.metaKey}>发表时间</Text>
                <Text style={styles.metaValue}>{paper.published_date}</Text>
              </View>
            ) : null}
            <View style={styles.metaItem}>
              <Text style={styles.metaKey}>爬取时间</Text>
              <Text style={styles.metaValue}>{paper.crawled_at}</Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaKey}>来源</Text>
              <Text style={styles.metaValue} numberOfLines={2}>
                {paper.journal_url}
              </Text>
            </View>
          </View>
        </View>

        {/* Actions */}
        <View style={styles.actions}>
          {paper.paper_url ? (
            <TouchableOpacity
              style={styles.primaryBtn}
              onPress={() => openLink(paper.paper_url)}
              activeOpacity={0.8}
            >
              <Text style={styles.primaryBtnText}>🔗 查看原文</Text>
            </TouchableOpacity>
          ) : null}

          {paper.doi ? (
            <TouchableOpacity
              style={styles.secondaryBtn}
              onPress={() => openLink(`https://doi.org/${paper.doi}`)}
              activeOpacity={0.8}
            >
              <Text style={styles.secondaryBtnText}>🌐 通过 DOI 打开</Text>
            </TouchableOpacity>
          ) : null}

          <TouchableOpacity
            style={styles.shareBtn}
            onPress={handleShare}
            activeOpacity={0.8}
          >
            <Text style={styles.shareBtnText}>📤 分享</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
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
    backgroundColor: '#F8FAFC',
  },
  errorText: {
    fontSize: 16,
    color: '#94A3B8',
  },
  scroll: {
    flex: 1,
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1E293B',
    lineHeight: 30,
  },
  section: {
    marginTop: 20,
  },
  label: {
    fontSize: 15,
    fontWeight: '600',
    color: '#475569',
    marginBottom: 8,
  },
  authorsSection: {
    marginTop: 16,
  },
  authorList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  authorBadge: {
    backgroundColor: '#EFF6FF',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#BFDBFE',
  },
  authorText: {
    fontSize: 13,
    color: '#1D4ED8',
  },
  abstract: {
    fontSize: 15,
    color: '#334155',
    lineHeight: 24,
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#F1F5F9',
    overflow: 'hidden',
  },
  metaGrid: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F1F5F9',
    gap: 12,
  },
  metaItem: {
    gap: 2,
  },
  metaKey: {
    fontSize: 12,
    color: '#94A3B8',
  },
  metaValue: {
    fontSize: 14,
    color: '#1E293B',
  },
  actions: {
    marginTop: 24,
    gap: 10,
  },
  primaryBtn: {
    backgroundColor: '#2563EB',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  primaryBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryBtn: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
  },
  secondaryBtnText: {
    color: '#475569',
    fontSize: 16,
    fontWeight: '600',
  },
  shareBtn: {
    backgroundColor: '#F1F5F9',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  shareBtnText: {
    color: '#64748B',
    fontSize: 16,
    fontWeight: '600',
  },
});
