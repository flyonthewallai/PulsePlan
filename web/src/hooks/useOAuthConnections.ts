import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { oauthService } from '../services/oauthService'
import type { OAuthConnection, OAuthProvider, OAuthService } from '../services/oauthService'
import { OAUTH_CACHE_KEYS } from './cacheKeys'

export function useOAuthConnections() {
  const queryClient = useQueryClient()

  const {
    data: connections = [],
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: OAUTH_CACHE_KEYS.CONNECTIONS,
    queryFn: oauthService.getOAuthConnections,
    retry: 2,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const connectMutation = useMutation({
    mutationFn: ({ provider, service }: { provider: OAuthProvider; service?: OAuthService }) =>
      oauthService.connectProvider(provider, service),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: OAUTH_CACHE_KEYS.CONNECTIONS })
    },
  })

  const disconnectMutation = useMutation({
    mutationFn: (provider: OAuthProvider) => oauthService.disconnectOAuth(provider),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: OAUTH_CACHE_KEYS.CONNECTIONS })
    },
  })

  const connect = async (provider: OAuthProvider, service?: OAuthService) => {
    return await connectMutation.mutateAsync({ provider, service })
  }

  const disconnect = async (provider: OAuthProvider) => {
    return await disconnectMutation.mutateAsync(provider)
  }

  const getConnectionStatus = (provider: OAuthProvider): OAuthConnection | undefined => {
    return connections.find(conn => conn.provider === provider)
  }

  const isConnected = (provider: OAuthProvider): boolean => {
    return getConnectionStatus(provider)?.connected ?? false
  }

  return {
    connections,
    isLoading,
    error,
    refetch,
    connect,
    disconnect,
    getConnectionStatus,
    isConnected,
    isConnecting: connectMutation.isPending,
    isDisconnecting: disconnectMutation.isPending,
    connectError: connectMutation.error,
    disconnectError: disconnectMutation.error,
  }
}