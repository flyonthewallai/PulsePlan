import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { oauthService } from '@/services/integrations'
import type { OAuthConnection, OAuthProvider, OAuthService } from '@/services/integrations'
import { OAUTH_CACHE_KEYS } from '@/hooks/shared/cacheKeys'

export function useOAuthConnections() {
  const queryClient = useQueryClient()

  const {
    data: connections = [],
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: OAUTH_CACHE_KEYS.CONNECTIONS,
    queryFn: async () => {
      return await oauthService.getOAuthConnections()
    },
    retry: 2,
    staleTime: 10000, // 10 seconds - prevent constant refetching, rely on WebSocket for updates
    refetchOnWindowFocus: true, // Still refetch on focus for user-initiated tab switches
  })

  const connectMutation = useMutation({
    mutationFn: ({ provider, service }: { provider: OAuthProvider; service?: OAuthService }) =>
      oauthService.connectProvider(provider, service),
    onSuccess: async () => {
      // Invalidate and immediately refetch to update connection status
      // Using refetchType: 'all' ensures even inactive queries are refetched
      await queryClient.invalidateQueries({
        queryKey: OAUTH_CACHE_KEYS.CONNECTIONS,
        refetchType: 'all'
      })
    },
  })

  const disconnectMutation = useMutation({
    mutationFn: ({ provider, service }: { provider: OAuthProvider; service: OAuthService }) =>
      oauthService.disconnectOAuth(provider, service),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: OAUTH_CACHE_KEYS.CONNECTIONS })
    },
  })

  const connect = async (provider: OAuthProvider, service?: OAuthService) => {
    return await connectMutation.mutateAsync({ provider, service })
  }

  const disconnect = async (provider: OAuthProvider, service: OAuthService) => {
    return await disconnectMutation.mutateAsync({ provider, service })
  }

  const getConnectionStatus = (provider: OAuthProvider, service?: OAuthService): OAuthConnection | undefined => {
    if (service) {
      return connections.find(conn => conn.provider === provider && conn.service === service)
    }
    // If no service specified, return first connection for provider
    return connections.find(conn => conn.provider === provider)
  }

  const isConnected = (provider: OAuthProvider, service?: OAuthService): boolean => {
    return getConnectionStatus(provider, service)?.connected ?? false
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