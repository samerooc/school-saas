// lib/services/auth_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:local_auth/local_auth.dart';
import 'api_service.dart';

// ── Auth State ────────────────────────────────────────────────────────────────

class AuthState {
  final bool isLoading;
  final bool isAuthenticated;
  final String? role;
  final String? userId;
  final String? fullName;
  final String? error;

  const AuthState({
    this.isLoading = true,
    this.isAuthenticated = false,
    this.role,
    this.userId,
    this.fullName,
    this.error,
  });

  AuthState copyWith({
    bool? isLoading, bool? isAuthenticated,
    String? role, String? userId, String? fullName, String? error,
  }) => AuthState(
    isLoading: isLoading ?? this.isLoading,
    isAuthenticated: isAuthenticated ?? this.isAuthenticated,
    role: role ?? this.role,
    userId: userId ?? this.userId,
    fullName: fullName ?? this.fullName,
    error: error ?? this.error,
  );
}

// ── Auth Notifier ─────────────────────────────────────────────────────────────

class AuthNotifier extends StateNotifier<AuthState> {
  final ApiService _api;
  final LocalAuthentication _localAuth = LocalAuthentication();

  AuthNotifier(this._api) : super(const AuthState()) {
    _checkExistingSession();
  }

  Future<void> _checkExistingSession() async {
    final token = await SecureTokenStorage.getAccessToken();
    final role = await SecureTokenStorage.getRole();
    final userId = await SecureTokenStorage.getUserId();
    final fullName = await SecureTokenStorage.getFullName();

    if (token != null && role != null) {
      state = state.copyWith(
        isLoading: false,
        isAuthenticated: true,
        role: role,
        userId: userId,
        fullName: fullName,
      );
    } else {
      state = state.copyWith(isLoading: false, isAuthenticated: false);
    }
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final data = await _api.login(email, password);
      state = state.copyWith(
        isLoading: false,
        isAuthenticated: true,
        role: data['role'],
        userId: data['user_id'],
        fullName: data['full_name'],
      );
    } catch (e) {
      String msg = 'Login failed';
      if (e.toString().contains('401')) msg = 'Invalid email or password';
      if (e.toString().contains('423')) msg = 'Account locked. Try after 30 minutes';
      state = state.copyWith(isLoading: false, error: msg);
    }
  }

  // Biometric re-auth (app foreground gate)
  Future<bool> authenticateWithBiometrics() async {
    try {
      final canAuth = await _localAuth.canCheckBiometrics;
      if (!canAuth) return true; // No biometrics available — skip

      return await _localAuth.authenticate(
        localizedReason: 'Verify your identity to continue',
        options: const AuthenticationOptions(
          biometricOnly: false, // Allow PIN fallback
          stickyAuth: true,
        ),
      );
    } catch (_) {
      return false;
    }
  }

  Future<void> logout() async {
    await _api.logout();
    state = const AuthState(isLoading: false, isAuthenticated: false);
  }
}

// ── Providers ─────────────────────────────────────────────────────────────────

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.watch(apiServiceProvider));
});

// Helper getters
final isAuthenticatedProvider = Provider<bool>((ref) =>
  ref.watch(authProvider).isAuthenticated
);

final userRoleProvider = Provider<String?>((ref) =>
  ref.watch(authProvider).role
);
