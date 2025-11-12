import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { hobbiesApi, type Hobby, type CreateHobbyRequest } from '@/lib/api/sdk'

export const HOBBIES_QUERY_KEY = 'hobbies'

export function useHobbies(includeInactive = false) {
  return useQuery({
    queryKey: [HOBBIES_QUERY_KEY, includeInactive],
    queryFn: () => hobbiesApi.list(includeInactive),
  })
}

export function useHobby(id: string) {
  return useQuery({
    queryKey: [HOBBIES_QUERY_KEY, id],
    queryFn: () => hobbiesApi.get(id),
    enabled: !!id,
  })
}

export function useCreateHobby() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (hobby: CreateHobbyRequest) => hobbiesApi.create(hobby),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [HOBBIES_QUERY_KEY] })
    },
  })
}

export function useUpdateHobby() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<CreateHobbyRequest> }) =>
      hobbiesApi.update(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [HOBBIES_QUERY_KEY] })
    },
  })
}

export function useDeleteHobby() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, permanent = false }: { id: string; permanent?: boolean }) =>
      hobbiesApi.delete(id, permanent),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [HOBBIES_QUERY_KEY] })
    },
  })
}
