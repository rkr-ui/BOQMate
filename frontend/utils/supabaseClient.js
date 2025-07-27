import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// Mock Supabase client for development/testing
const createMockSupabaseClient = () => ({
  auth: {
    getSession: async () => ({
      data: {
        session: {
          user: {
            id: 'mock-user-id',
            email: 'test@example.com',
            phone: '+1234567890'
          }
        }
      }
    }),
    onAuthStateChange: (callback) => {
      // Mock subscription
      return {
        data: {
          subscription: {
            unsubscribe: () => {}
          }
        }
      };
    },
    signUp: async ({ email, password, phone, options }) => ({ 
      error: null,
      data: {
        user: {
          id: 'mock-user-id',
          email,
          phone
        }
      }
    }),
    signInWithPassword: async ({ email, password }) => ({ 
      error: null,
      data: {
        user: {
          id: 'mock-user-id',
          email
        }
      }
    }),
    signInWithOAuth: async ({ provider, options }) => {
      // Simulate OAuth redirect
      if (typeof window !== 'undefined') {
        window.location.href = options.redirectTo;
      }
      return { error: null };
    },
    signInWithOtp: async ({ phone, options }) => {
      // Mock OTP sending
      console.log(`Mock OTP sent to ${phone}`);
      return { error: null };
    },
    verifyOtp: async ({ phone, token, type }) => {
      // Mock OTP verification (accept any 6-digit code)
      if (token && token.length === 6 && /^\d+$/.test(token)) {
        return { 
          error: null,
          data: {
            user: {
              id: 'mock-user-id',
              phone
            }
          }
        };
      }
      return { error: { message: 'Invalid OTP' } };
    },
    resetPasswordForEmail: async (email, options) => {
      // Mock password reset email
      console.log(`Mock password reset email sent to ${email}`);
      return { error: null };
    },
    updateUser: async ({ password }) => {
      // Mock password update
      console.log('Mock password updated');
      return { error: null };
    },
    resend: async ({ type, email, options }) => {
      // Mock resend verification email
      console.log(`Mock ${type} email resent to ${email}`);
      return { error: null };
    },
    signOut: async () => ({ error: null })
  }
});

// Helper function to validate URL
const isValidUrl = (url) => {
  if (!url || url === 'your-supabase-project-url') return false;
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

// Use real Supabase if credentials are provided and valid, otherwise use mock
export const supabase = (isValidUrl(supabaseUrl) && supabaseAnonKey && supabaseAnonKey !== 'your-supabase-anon-key')
  ? createClient(supabaseUrl, supabaseAnonKey)
  : createMockSupabaseClient();

// Helper function to check if Supabase is available
export const isSupabaseAvailable = () => {
  return isValidUrl(supabaseUrl) && supabaseAnonKey && supabaseAnonKey !== 'your-supabase-anon-key';
}; 