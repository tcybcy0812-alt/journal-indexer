import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface Paper {
  id: number;
  title: string;
  authors: string[];
  abstract: string;
  paper_url: string;
  doi: string;
  published_date: string;
}

export default function PaperCard({ paper, onPress }: { paper: Paper; onPress: () => void }) {
  const authorsText = paper.authors.slice(0, 3).join(', ');
  const hasMore = paper.authors.length > 3;

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.cardBody}>
        <Text style={styles.title} numberOfLines={2}>
          {paper.title}
        </Text>

        {authorsText ? (
          <Text style={styles.authors} numberOfLines={1}>
            {authorsText}
            {hasMore ? ` 等 ${paper.authors.length} 位` : ''}
          </Text>
        ) : null}

        {paper.abstract ? (
          <Text style={styles.abstract} numberOfLines={3}>
            {paper.abstract}
          </Text>
        ) : null}

        <View style={styles.meta}>
          {paper.doi ? (
            <Text style={styles.doi} numberOfLines={1}>
              DOI: {paper.doi}
            </Text>
          ) : null}
        </View>
      </View>

      <View style={styles.arrow}>
        <Text style={styles.arrowText}>›</Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    marginTop: 10,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#F1F5F9',
  },
  cardBody: {
    flex: 1,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1E293B',
    lineHeight: 22,
  },
  authors: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 6,
  },
  abstract: {
    fontSize: 13,
    color: '#94A3B8',
    marginTop: 6,
    lineHeight: 19,
  },
  meta: {
    marginTop: 8,
    flexDirection: 'row',
    gap: 8,
  },
  doi: {
    fontSize: 11,
    color: '#94A3B8',
    flex: 1,
  },
  arrow: {
    marginLeft: 8,
  },
  arrowText: {
    fontSize: 24,
    color: '#CBD5E1',
    fontWeight: '300',
  },
});
