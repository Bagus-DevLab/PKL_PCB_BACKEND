import { useState, useEffect, useCallback } from "react";
import { auth } from "@/lib/firebase";
import {
  signInWithEmailAndPassword,
  signOut,
} from "firebase/auth";
import { authApi, userApi } from "@/lib/api";

export function useAuth() {
  const [user, setUser] = useState(null); // user info dari backend
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Cek apakah sudah ada session tersimpan di localStorage
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const savedUser = localStorage.getItem("user_info");

    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem("user_info");
      }
    }
    setLoading(false);
  }, []);

  // Login dengan email + password via Firebase, lalu kirim token ke backend
  const login = useCallback(async (email, password) => {
    setLoading(true);
    setError(null);

    try {
      // 1. Login ke Firebase
      const credential = await signInWithEmailAndPassword(auth, email, password);
      const idToken = await credential.user.getIdToken();

      // 2. Kirim Firebase token ke backend → dapat JWT lokal
      const response = await authApi.loginWithFirebase(idToken);
      const { access_token } = response.data;

      // 3. Cek role — harus admin
      localStorage.setItem("access_token", access_token);
      const meResponse = await userApi.getMe();
      const fullUser = meResponse.data;

      if (fullUser.role !== "admin") {
        // Bukan admin — hapus token dan tolak
        localStorage.removeItem("access_token");
        await signOut(auth);
        throw new Error("Akses ditolak. Akun ini bukan admin.");
      }

      // 4. Simpan session
      localStorage.setItem("user_info", JSON.stringify(fullUser));
      setUser(fullUser);

      return fullUser;
    } catch (err) {
      const message =
        err.message ||
        err.response?.data?.detail ||
        "Login gagal. Periksa email dan password.";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Logout
  const logout = useCallback(async () => {
    try {
      await signOut(auth);
    } catch {
      // Ignore Firebase signout errors
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_info");
    setUser(null);
  }, []);

  // Cek apakah user adalah admin
  const isAdmin = user?.role === "admin";
  const isAuthenticated = !!user && !!localStorage.getItem("access_token");

  return {
    user,
    loading,
    error,
    isAdmin,
    isAuthenticated,
    login,
    logout,
    setError,
  };
}
