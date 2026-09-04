import axios from 'axios';
import { PredictionRun, ExplanationResponse, ValidationResult } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getPredictions = async (diseaseId: string, topK: number = 10): Promise<PredictionRun> => {
  const response = await api.get(`/predictions/${diseaseId}?top_k=${topK}`);
  return response.data;
};

export const getExplanations = async (predictionId: string): Promise<ExplanationResponse> => {
  const response = await api.get(`/explanations/${predictionId}`);
  return response.data;
};

export const getValidation = async (predictionId: string): Promise<ValidationResult> => {
  const response = await api.get(`/validation/${predictionId}`);
  return response.data;
};

export default api;
