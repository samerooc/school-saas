// lib/services/api_service.dart
// Dio HTTP client with:
// 1. Auto-attach Bearer token from secure storage
// 2. 401 → silent token refresh → retry
// 3. Certificate pinning ready
// 4. Never log tokens/passwords

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

// ── Constants ─────────────────────────────────────────────────────────────────

const String _baseUrl = String.fromEnvironment(
  'API_URL',
  defaultValue: 'https://your-app.railway.app/api',
);

// Secure storage keys
const _kAccessToken  = 'access_token';
const _kRefreshToken = 'refresh_token';
const _kUserRole     = 'user_role';
const _kUserId       = 'user_id';
const _kFullName     = 'full_name';

// ── Secure Storage ────────────────────────────────────────────────────────────

class SecureTokenStorage {
  static const _storage = FlutterSecureStorage(
    // Android: uses Keystore (encrypted)
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
    // iOS: uses Keychain
    iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
  );

  static Future<void> saveTokens({
    required String accessToken,
    required String role,
    required String userId,
    required String fullName,
  }) async {
    await Future.wait([
      _storage.write(key: _kAccessToken, value: accessToken),
      _storage.write(key: _kUserRole, value: role),
      _storage.write(key: _kUserId, value: userId),
      _storage.write(key: _kFullName, value: fullName),
    ]);
  }

  static Future<String?> getAccessToken() => _storage.read(key: _kAccessToken);
  static Future<String?> getRole() => _storage.read(key: _kUserRole);
  static Future<String?> getUserId() => _storage.read(key: _kUserId);
  static Future<String?> getFullName() => _storage.read(key: _kFullName);

  static Future<void> clearAll() async {
    await _storage.deleteAll();
  }
}

// ── API Client ────────────────────────────────────────────────────────────────

class ApiService {
  late final Dio _dio;
  bool _isRefreshing = false;
  final List<RequestOptions> _pendingRequests = [];

  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
    ));

    // Add auth interceptor
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: _onRequest,
      onError: _onError,
    ));
  }

  Future<void> _onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // Attach Bearer token to every request
    final token = await SecureTokenStorage.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    // Never log auth headers in production
    handler.next(options);
  }

  Future<void> _onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401 && !_isRefreshing) {
      _isRefreshing = true;
      try {
        // Attempt token refresh
        final refreshed = await _refreshToken();
        if (refreshed) {
          // Retry original request with new token
          final token = await SecureTokenStorage.getAccessToken();
          final opts = err.requestOptions;
          opts.headers['Authorization'] = 'Bearer $token';
          final response = await _dio.fetch(opts);
          handler.resolve(response);
          return;
        }
      } catch (_) {
        // Refresh failed — clear storage, trigger logout
        await SecureTokenStorage.clearAll();
      } finally {
        _isRefreshing = false;
      }
    }
    handler.next(err);
  }

  Future<bool> _refreshToken() async {
    try {
      // Cookie sent automatically by dio (set withCredentials)
      final response = await Dio().post('$_baseUrl/auth/refresh');
      final data = response.data;
      await SecureTokenStorage.saveTokens(
        accessToken: data['access_token'],
        role: data['role'],
        userId: data['user_id'],
        fullName: data['full_name'],
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  // ── Auth endpoints ───────────────────────────────────────────────────────

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await _dio.post('/auth/login', data: {
      'email': email,
      'password': password,
    });
    final data = response.data as Map<String, dynamic>;
    // Save token to Keystore/Keychain
    await SecureTokenStorage.saveTokens(
      accessToken: data['access_token'],
      role: data['role'],
      userId: data['user_id'],
      fullName: data['full_name'],
    );
    return data;
  }

  Future<void> logout() async {
    try { await _dio.post('/auth/logout'); } catch (_) {}
    await SecureTokenStorage.clearAll();
  }

  // ── Students ─────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getStudents({
    int page = 1, String? search, String? classId
  }) async {
    final res = await _dio.get('/students', queryParameters: {
      'page': page, 'per_page': 20,
      if (search != null) 'search': search,
      if (classId != null) 'class_id': classId,
    });
    return res.data;
  }

  // ── Attendance ────────────────────────────────────────────────────────────

  Future<void> markAttendance({
    required String classId,
    required String date,
    required List<Map<String, String>> entries,
  }) async {
    await _dio.post('/attendance/bulk', data: {
      'class_id': classId,
      'date': date,
      'entries': entries,
    });
  }

  Future<Map<String, dynamic>> getStudentAttendance(String studentId) async {
    final res = await _dio.get('/attendance/student/$studentId');
    return res.data;
  }

  // ── Videos ────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getVideos({String? classId}) async {
    final res = await _dio.get('/videos', queryParameters: {
      if (classId != null) 'class_id': classId,
    });
    return res.data;
  }

  Future<Map<String, dynamic>> getVideoPlayerToken(String videoId) async {
    final res = await _dio.get('/videos/$videoId/player-token');
    return res.data;
  }

  Future<void> updateVideoProgress({
    required String videoId,
    required int watchedSeconds,
    int? totalSeconds,
  }) async {
    await _dio.post('/videos/$videoId/progress', queryParameters: {
      'watched_seconds': watchedSeconds,
      if (totalSeconds != null) 'total_seconds': totalSeconds,
    });
  }

  // ── Fees ─────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getStudentDues(String studentId) async {
    final res = await _dio.get('/fees/student/$studentId/dues');
    return res.data;
  }

  Future<Map<String, dynamic>> createRazorpayOrder({
    required String studentId,
    required String feeStructureId,
  }) async {
    final res = await _dio.post('/fees/razorpay/create-order',
      queryParameters: {'student_id': studentId, 'fee_structure_id': feeStructureId}
    );
    return res.data;
  }

  // ── Exams ─────────────────────────────────────────────────────────────────

  Future<List<dynamic>> getExams() async {
    final res = await _dio.get('/exams');
    return res.data;
  }

  Future<Map<String, dynamic>> getStudentResults(
    String examId, String studentId) async {
    final res = await _dio.get('/exams/$examId/results/$studentId');
    return res.data;
  }

  // ── Notices ───────────────────────────────────────────────────────────────

  Future<List<dynamic>> getNotices() async {
    final res = await _dio.get('/notices');
    return res.data;
  }

  // ── Classes ───────────────────────────────────────────────────────────────

  Future<List<dynamic>> getClasses() async {
    final res = await _dio.get('/classes');
    return res.data;
  }
}

// ── Provider ─────────────────────────────────────────────────────────────────

final apiServiceProvider = Provider<ApiService>((ref) => ApiService());
