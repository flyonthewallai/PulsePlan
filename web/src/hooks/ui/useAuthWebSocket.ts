import { useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { useWebSocket } from '@/contexts/WebSocketContext';

export function useAuthWebSocket() {
  const { setUserId } = useWebSocket();

  useEffect(() => {
    // Get initial session
    const getInitialSession = async () => {
      console.log('🔍 Getting initial Supabase session...');
      const { data: { session }, error } = await supabase.auth.getSession();

      if (error) {
        console.error('❌ Error getting session:', error);
        return;
      }

      if (session?.user?.id) {
        console.log('✅ Found authenticated user:', session.user.id);
        setUserId(session.user.id);
      } else {
        console.log('❌ No authenticated user found');
        setUserId(null);
      }
    };

    getInitialSession();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        console.log('Auth state changed:', event, session?.user?.id);
        if (session?.user?.id) {
          setUserId(session.user.id);
        } else {
          setUserId(null);
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [setUserId]);
}

