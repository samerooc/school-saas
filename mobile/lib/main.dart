import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'services/auth_provider.dart';
import 'screens/auth/login_screen.dart';
import 'screens/admin/admin_shell.dart';
import 'screens/teacher/teacher_shell.dart';
import 'screens/student/student_shell.dart';
import 'screens/parent/parent_shell.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  await Hive.initFlutter();
  runApp(const ProviderScope(child: SchoolSaaSApp()));
}

class SchoolSaaSApp extends ConsumerWidget {
  const SchoolSaaSApp({super.key});

  String _homeRoute(String? role) {
    switch (role) {
      case 'admin':
      case 'principal': return '/admin';
      case 'teacher':   return '/staff';
      case 'parent':    return '/parent';
      default:          return '/student';
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);

    final router = GoRouter(
      initialLocation: auth.isAuthenticated ? _homeRoute(auth.role) : '/login',
      redirect: (context, state) {
        final authed  = auth.isAuthenticated;
        final onLogin = state.matchedLocation == '/login';
        if (auth.isLoading) return null;
        if (!authed && !onLogin) return '/login';
        if (authed && onLogin) return _homeRoute(auth.role);
        return null;
      },
      routes: [
        GoRoute(path: '/login',   builder: (_, __) => const LoginScreen()),
        GoRoute(path: '/admin',   builder: (_, __) => const AdminShell()),
        GoRoute(path: '/staff',   builder: (_, __) => const TeacherShell()),
        GoRoute(path: '/student', builder: (_, __) => const StudentShell()),
        GoRoute(path: '/parent',  builder: (_, __) => const ParentShell()),
      ],
    );

    return MaterialApp.router(
      title: 'SchoolSaaS',
      debugShowCheckedModeBanner: false,
      routerConfig: router,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF4F46E5),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF030712),
        cardColor: const Color(0xFF111827),
        navigationBarTheme: const NavigationBarThemeData(
          backgroundColor: Color(0xFF111827),
          indicatorColor: Color(0x334F46E5),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF111827),
          foregroundColor: Colors.white,
          elevation: 0,
        ),
        useMaterial3: true,
      ),
    );
  }
}
