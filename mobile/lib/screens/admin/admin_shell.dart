// lib/screens/admin/admin_shell.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../services/auth_provider.dart';

class AdminShell extends ConsumerWidget {
  const AdminShell({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin Portal', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF111827),
        actions: [IconButton(icon: const Icon(Icons.logout), onPressed: () => ref.read(authProvider.notifier).logout())],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Welcome, ${auth.fullName ?? 'Admin'}!',
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(height: 20),
          Expanded(
            child: GridView.count(
              crossAxisCount: 2, crossAxisSpacing: 12, mainAxisSpacing: 12, childAspectRatio: 1.3,
              children: const [
                _AdminCard(icon: Icons.school, label: 'Students',  color: Color(0xFF4F46E5)),
                _AdminCard(icon: Icons.people, label: 'Staff',     color: Color(0xFF7C3AED)),
                _AdminCard(icon: Icons.payment, label: 'Fees',     color: Color(0xFFD97706)),
                _AdminCard(icon: Icons.bar_chart, label: 'Reports', color: Color(0xFF059669)),
              ],
            ),
          ),
        ]),
      ),
    );
  }
}

class _AdminCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  const _AdminCard({required this.icon, required this.label, required this.color});
  @override
  Widget build(BuildContext context) {
    return Card(
      color: color.withOpacity(0.1),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: color.withOpacity(0.3)),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {},
        child: Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Icon(icon, color: color, size: 32),
          const SizedBox(height: 8),
          Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500)),
        ])),
      ),
    );
  }
}
