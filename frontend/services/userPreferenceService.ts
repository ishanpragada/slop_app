import { API_CONFIG } from '../config/api';

const API_BASE_URL = API_CONFIG.BASE_URL;

export interface UserInteractionRequest {
  user_id: string;
  video_id: string;
  action: 'like' | 'view' | 'skip';
  timestamp?: string;
  metadata?: Record<string, any>;
}

export interface UserPreferenceResponse {
  success: boolean;
  message: string;
  preference_updated: boolean;
  interactions_since_update: number;
  timestamp: string;
}

export interface UserPreference {
  user_id: string;
  preference_embedding: number[];
  window_size: number;
  last_updated: string;
  interactions_since_update: number;
}

export interface UserInteraction {
  video_id: string;
  embedding: number[];
  type: string;
  weight: number;
  timestamp: string;
}

export interface UserInteractionWindow {
  user_id: string;
  interactions: UserInteraction[];
  last_updated: string;
}

class UserPreferenceService {
  /**
   * Track a user interaction for preference learning
   */
  async trackInteraction(request: UserInteractionRequest): Promise<UserPreferenceResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/user-preference/interaction`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...request,
          timestamp: request.timestamp || new Date().toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error tracking user interaction:', error);
      throw error;
    }
  }

  /**
   * Track a like interaction
   */
  async trackLike(userId: string, videoId: string): Promise<UserPreferenceResponse> {
    return this.trackInteraction({
      user_id: userId,
      video_id: videoId,
      action: 'like',
    });
  }

  /**
   * Track a view interaction (3+ seconds)
   */
  async trackView(userId: string, videoId: string): Promise<UserPreferenceResponse> {
    return this.trackInteraction({
      user_id: userId,
      video_id: videoId,
      action: 'view',
    });
  }

  /**
   * Track a skip interaction (<3 seconds)
   */
  async trackSkip(userId: string, videoId: string): Promise<UserPreferenceResponse> {
    return this.trackInteraction({
      user_id: userId,
      video_id: videoId,
      action: 'skip',
    });
  }

  /**
   * Get user's current preference vector
   */
  async getUserPreference(userId: string): Promise<UserPreference | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/user-preference/${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.success ? data.preference : null;
    } catch (error) {
      console.error('Error getting user preference:', error);
      throw error;
    }
  }

  /**
   * Get user's current interaction window
   */
  async getUserInteractions(userId: string): Promise<UserInteractionWindow | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/user-preference/${userId}/interactions`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.success ? data.interactions : null;
    } catch (error) {
      console.error('Error getting user interactions:', error);
      throw error;
    }
  }
}

export const userPreferenceService = new UserPreferenceService();
