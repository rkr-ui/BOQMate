import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../utils/supabaseClient';

const AuthContext = createContext({});

export const useAuth = () => {
  return useContext(AuthContext);
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [verificationSent, setVerificationSent] = useState(false);

  useEffect(() => {
    // Get initial session
    const getSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setUser(session?.user ?? null);
      setLoading(false);
    };

    getSession();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setUser(session?.user ?? null);
        setLoading(false);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  // Email/Password Authentication
  const signUp = async (email, password, phone = null) => {
    const { error } = await supabase.auth.signUp({ 
      email, 
      password,
      phone,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`
      }
    });
    return { error };
  };

  const signIn = async (email, password) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    return { error };
  };

  const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    return { error };
  };

  // Social Authentication
  const signInWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    });
    return { error };
  };

  const signInWithApple = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'apple',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    });
    return { error };
  };

  const signInWithLinkedIn = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'linkedin',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    });
    return { error };
  };

  // Phone Verification
  const sendPhoneVerification = async (phone) => {
    const { error } = await supabase.auth.signInWithOtp({
      phone,
      options: {
        shouldCreateUser: true
      }
    });
    if (!error) {
      setVerificationSent(true);
    }
    return { error };
  };

  const verifyPhoneOTP = async (phone, token) => {
    const { error } = await supabase.auth.verifyOtp({
      phone,
      token,
      type: 'sms'
    });
    return { error };
  };

  // Password Recovery
  const resetPassword = async (email) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/reset-password`
    });
    return { error };
  };

  const updatePassword = async (newPassword) => {
    const { error } = await supabase.auth.updateUser({
      password: newPassword
    });
    return { error };
  };

  // Email Verification
  const resendVerificationEmail = async (email) => {
    const { error } = await supabase.auth.resend({
      type: 'signup',
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`
      }
    });
    return { error };
  };

  const value = {
    user,
    loading,
    verificationSent,
    signUp,
    signIn,
    signOut,
    signInWithGoogle,
    signInWithApple,
    signInWithLinkedIn,
    sendPhoneVerification,
    verifyPhoneOTP,
    resetPassword,
    updatePassword,
    resendVerificationEmail,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 