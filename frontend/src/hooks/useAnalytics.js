/**
 * useAnalytics.js - Custom hook for analytics and dashboard data
 * Fetches KPIs, charts data, and statistics from backend
 */

import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { toast } from 'react-hot-toast';

export const useAnalytics = (autoRefresh = false, refreshInterval = 30000) => {
  const [overview, setOverview] = useState(null);
  const [volume, setVolume] = useState(null);
  const [categories, setCategories] = useState(null);
  const [confidence, setConfidence] = useState(null);
  const [resolutionFunnel, setResolutionFunnel] = useState(null);
  const [sentiment, setSentiment] = useState(null);
  const [sla, setSla] = useState(null);
  const [agents, setAgents] = useState(null);
  const [domains, setDomains] = useState(null);
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch overview KPIs
  const fetchOverview = useCallback(async () => {
    try {
      const response = await api.get('/analytics/overview');
      setOverview(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch overview:', err);
      throw err;
    }
  }, []);

  // Fetch ticket volume over time
  const fetchVolume = useCallback(async (days = 7) => {
    try {
      const response = await api.get('/analytics/volume', {
        params: { days }
      });
      setVolume(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch volume:', err);
      throw err;
    }
  }, []);

  // Fetch category distribution
  const fetchCategories = useCallback(async () => {
    try {
      const response = await api.get('/analytics/categories');
      setCategories(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch categories:', err);
      throw err;
    }
  }, []);

  // Fetch confidence distribution
  const fetchConfidence = useCallback(async () => {
    try {
      const response = await api.get('/analytics/confidence');
      setConfidence(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch confidence:', err);
      throw err;
    }
  }, []);

  // Fetch resolution funnel
  const fetchResolutionFunnel = useCallback(async () => {
    try {
      const response = await api.get('/analytics/resolution-funnel');
      setResolutionFunnel(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch resolution funnel:', err);
      throw err;
    }
  }, []);

  // Fetch sentiment trends
  const fetchSentiment = useCallback(async (hours = 24) => {
    try {
      const response = await api.get('/analytics/sentiment', {
        params: { hours }
      });
      setSentiment(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch sentiment:', err);
      throw err;
    }
  }, []);

  // Fetch SLA statistics
  const fetchSLA = useCallback(async () => {
    try {
      const response = await api.get('/analytics/sla');
      setSla(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch SLA:', err);
      throw err;
    }
  }, []);

  // Fetch agent performance
  const fetchAgents = useCallback(async () => {
    try {
      const response = await api.get('/analytics/agents');
      setAgents(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch agents:', err);
      throw err;
    }
  }, []);

  // Fetch domain statistics
  const fetchDomains = useCallback(async () => {
    try {
      const response = await api.get('/analytics/domains');
      setDomains(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch domains:', err);
      throw err;
    }
  }, []);

  // Fetch volume predictions
  const fetchPredictions = useCallback(async () => {
    try {
      const response = await api.get('/analytics/predictions');
      setPredictions(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch predictions:', err);
      throw err;
    }
  }, []);

  // Fetch all analytics data
  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      await Promise.all([
        fetchOverview(),
        fetchVolume(),
        fetchCategories(),
        fetchConfidence(),
        fetchResolutionFunnel(),
        fetchSentiment(),
        fetchSLA(),
        fetchAgents(),
        fetchDomains(),
        fetchPredictions()
      ]);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
      setError(err.response?.data?.detail || 'Failed to fetch analytics');
      toast.error('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  }, [
    fetchOverview,
    fetchVolume,
    fetchCategories,
    fetchConfidence,
    fetchResolutionFunnel,
    fetchSentiment,
    fetchSLA,
    fetchAgents,
    fetchDomains,
    fetchPredictions
  ]);

  // Initial fetch
  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchAll();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchAll]);

  return {
    overview,
    volume,
    categories,
    confidence,
    resolutionFunnel,
    sentiment,
    sla,
    agents,
    domains,
    predictions,
    loading,
    error,
    fetchAll,
    fetchOverview,
    fetchVolume,
    fetchCategories,
    fetchConfidence,
    fetchResolutionFunnel,
    fetchSentiment,
    fetchSLA,
    fetchAgents,
    fetchDomains,
    fetchPredictions
  };
};

// Hook for ML model metrics
export const useMLMetrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [confusionMatrix, setConfusionMatrix] = useState(null);
  const [featureImportance, setFeatureImportance] = useState(null);
  const [calibration, setCalibration] = useState(null);
  const [versions, setVersions] = useState(null);
  const [retrainingStatus, setRetrainingStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchMetrics = useCallback(async () => {
    try {
      const response = await api.get('/ml/metrics');
      setMetrics(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch ML metrics:', err);
      throw err;
    }
  }, []);

  const fetchConfusionMatrix = useCallback(async () => {
    try {
      const response = await api.get('/ml/confusion-matrix');
      setConfusionMatrix(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch confusion matrix:', err);
      throw err;
    }
  }, []);

  const fetchFeatureImportance = useCallback(async () => {
    try {
      const response = await api.get('/ml/feature-importance');
      setFeatureImportance(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch feature importance:', err);
      throw err;
    }
  }, []);

  const fetchCalibration = useCallback(async () => {
    try {
      const response = await api.get('/ml/calibration');
      setCalibration(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch calibration:', err);
      throw err;
    }
  }, []);

  const fetchVersions = useCallback(async () => {
    try {
      const response = await api.get('/ml/versions');
      setVersions(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch versions:', err);
      throw err;
    }
  }, []);

  const fetchRetrainingStatus = useCallback(async () => {
    try {
      const response = await api.get('/ml/retraining-status');
      setRetrainingStatus(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch retraining status:', err);
      throw err;
    }
  }, []);

  const triggerRetraining = useCallback(async () => {
    try {
      const response = await api.post('/ml/retrain');
      toast.success('Model retraining started!');
      return response.data;
    } catch (err) {
      console.error('Failed to trigger retraining:', err);
      toast.error('Failed to start retraining');
      throw err;
    }
  }, []);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      await Promise.all([
        fetchMetrics(),
        fetchConfusionMatrix(),
        fetchFeatureImportance(),
        fetchCalibration(),
        fetchVersions(),
        fetchRetrainingStatus()
      ]);
    } catch (err) {
      console.error('Failed to fetch ML data:', err);
      setError(err.response?.data?.detail || 'Failed to fetch ML data');
      toast.error('Failed to load ML metrics');
    } finally {
      setLoading(false);
    }
  }, [
    fetchMetrics,
    fetchConfusionMatrix,
    fetchFeatureImportance,
    fetchCalibration,
    fetchVersions,
    fetchRetrainingStatus
  ]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return {
    metrics,
    confusionMatrix,
    featureImportance,
    calibration,
    versions,
    retrainingStatus,
    loading,
    error,
    fetchAll,
    triggerRetraining
  };
};
