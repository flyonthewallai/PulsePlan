import { API_BASE_URL } from '../config/api'
import { supabase } from '../lib/supabase'

export interface Tag {
  name: string
  category?: string
  type: 'predefined' | 'user'
  id?: string
  created_at?: string
}

export interface UserTag {
  id: string
  user_id: string
  name: string
  created_at: string
}

class TagsService {
  private async getAuthHeaders() {
    const { data: { session } } = await supabase.auth.getSession()
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session?.access_token}`,
    }
  }

  async getPredefinedTags(): Promise<Tag[]> {
    try {
      const headers = await this.getAuthHeaders()
      const response = await fetch(`${API_BASE_URL}/api/v1/tags/predefined`, {
        method: 'GET',
        headers,
      })

      if (!response.ok) {
        throw new Error('Failed to fetch predefined tags')
      }

      const result = await response.json()
      return result.data?.tags || []
    } catch (error) {
      console.error('Error fetching predefined tags:', error)
      return []
    }
  }

  async getUserTags(): Promise<Tag[]> {
    try {
      const headers = await this.getAuthHeaders()
      const response = await fetch(`${API_BASE_URL}/api/v1/tags/user`, {
        method: 'GET',
        headers,
      })

      if (!response.ok) {
        throw new Error('Failed to fetch user tags')
      }

      const result = await response.json()
      return result.data?.tags || []
    } catch (error) {
      console.error('Error fetching user tags:', error)
      return []
    }
  }

  async getAllTags(): Promise<Tag[]> {
    try {
      const headers = await this.getAuthHeaders()
      const response = await fetch(`${API_BASE_URL}/api/v1/tags/all`, {
        method: 'GET',
        headers,
      })

      if (!response.ok) {
        throw new Error('Failed to fetch all tags')
      }

      const result = await response.json()
      return result.data?.tags || []
    } catch (error) {
      console.error('Error fetching all tags:', error)
      return []
    }
  }

  async createUserTag(name: string): Promise<UserTag | null> {
    try {
      const headers = await this.getAuthHeaders()
      const response = await fetch(`${API_BASE_URL}/api/v1/tags/user`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ name }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to create tag')
      }

      const result = await response.json()
      return result.data?.tag || null
    } catch (error) {
      console.error('Error creating user tag:', error)
      throw error
    }
  }

  async deleteUserTag(tagId: string): Promise<boolean> {
    try {
      const headers = await this.getAuthHeaders()
      const response = await fetch(`${API_BASE_URL}/api/v1/tags/user/${tagId}`, {
        method: 'DELETE',
        headers,
      })

      if (!response.ok) {
        throw new Error('Failed to delete tag')
      }

      return true
    } catch (error) {
      console.error('Error deleting user tag:', error)
      return false
    }
  }

  async deleteUserTagByName(tagName: string): Promise<boolean> {
    try {
      // First get all user tags to find the ID
      const userTags = await this.getUserTags()
      const tag = userTags.find(t => t.name === tagName)
      
      if (!tag || !tag.id) {
        throw new Error('Tag not found')
      }

      return await this.deleteUserTag(tag.id)
    } catch (error) {
      console.error('Error deleting user tag by name:', error)
      return false
    }
  }
}

export const tagsApi = new TagsService()

