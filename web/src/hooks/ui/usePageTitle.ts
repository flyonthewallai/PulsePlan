import { useEffect } from 'react'

export function usePageTitle(pageName: string) {
  useEffect(() => {
    if (!pageName) return
    document.title = `${pageName} - PulsePlan`
  }, [pageName])
}




