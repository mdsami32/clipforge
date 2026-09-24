export interface TranscriptWord {
  word: string;
  start: number;
  end: number;
  confidence?: number;
}

export interface TranscriptSegment {
  id: number;
  start: number;
  end: number;
  text: string;
  words: TranscriptWord[];
}

export interface NormalizedTranscript {
  version: number;
  language?: string | null;
  duration: number;
  segments: TranscriptSegment[];
  words: TranscriptWord[];
}
