import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../services/auth_provider.dart';
import '../../services/api_service.dart';

class ParentShell extends ConsumerStatefulWidget {
  const ParentShell({super.key});
  @override
  ConsumerState<ParentShell> createState() => _ParentShellState();
}

class _ParentShellState extends ConsumerState<ParentShell> {
  int _index = 0;
  @override
  Widget build(BuildContext context) {
    final pages = [
      const ParentHomePage(),
      const ParentFeesPage(),
      const ParentBusPage(),
      const ParentNoticesPage(),
    ];
    return Scaffold(
      body: pages[_index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.payment_outlined), selectedIcon: Icon(Icons.payment), label: 'Fees'),
          NavigationDestination(icon: Icon(Icons.directions_bus_outlined), selectedIcon: Icon(Icons.directions_bus), label: 'Bus'),
          NavigationDestination(icon: Icon(Icons.notifications_outlined), selectedIcon: Icon(Icons.notifications), label: 'Notices'),
        ],
      ),
    );
  }
}

class ParentHomePage extends ConsumerWidget {
  const ParentHomePage({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Parent Portal', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [IconButton(icon: const Icon(Icons.logout), onPressed: () => ref.read(authProvider.notifier).logout())],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Welcome, ${auth.fullName?.split(' ').first ?? 'Parent'}! 👋',
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(height: 4),
          const Text("Monitor your child's progress", style: TextStyle(color: Colors.grey)),
          const SizedBox(height: 20),
          Expanded(child: GridView.count(
            crossAxisCount: 2, crossAxisSpacing: 12, mainAxisSpacing: 12, childAspectRatio: 1.2,
            children: const [
              _Card(icon: Icons.trending_up, label: "Child's Progress", color: Color(0xFF059669)),
              _Card(icon: Icons.payment, label: 'Pay Fees', color: Color(0xFFD97706)),
              _Card(icon: Icons.directions_bus, label: 'Track Bus', color: Color(0xFF4F46E5)),
              _Card(icon: Icons.notifications, label: 'Notices', color: Color(0xFF7C3AED)),
            ],
          )),
        ]),
      ),
    );
  }
}

class _Card extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  const _Card({required this.icon, required this.label, required this.color});
  @override
  Widget build(BuildContext context) {
    return Card(
      color: color.withOpacity(0.1),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: BorderSide(color: color.withOpacity(0.3))),
      child: InkWell(borderRadius: BorderRadius.circular(16), onTap: () {},
        child: Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Icon(icon, color: color, size: 30),
          const SizedBox(height: 8),
          Text(label, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w500)),
        ])),
      ),
    );
  }
}

class ParentFeesPage extends ConsumerStatefulWidget {
  const ParentFeesPage({super.key});
  @override
  ConsumerState<ParentFeesPage> createState() => _ParentFeesPageState();
}

class _ParentFeesPageState extends ConsumerState<ParentFeesPage> {
  Map<String, dynamic>? _fees;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadFees();
  }

  Future<void> _loadFees() async {
    try {
      final api = ref.read(apiServiceProvider);
      // TODO: Get student ID from auth/me
      final data = await api.getStudentDues('student-id-placeholder');
      setState(() { _fees = data; _loading = false; });
    } catch (_) { setState(() => _loading = false); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Fee Status', style: TextStyle(fontWeight: FontWeight.bold))),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _fees == null
          ? const Center(child: Text('Could not load fees', style: TextStyle(color: Colors.grey)))
          : Padding(
              padding: const EdgeInsets.all(16),
              child: Column(children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: const Color(0xFFD97706).withOpacity(0.1), borderRadius: BorderRadius.circular(16), border: Border.all(color: const Color(0xFFD97706).withOpacity(0.3))),
                  child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                    const Text('Total Due', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    Text('₹${_fees!['total_due']?.toStringAsFixed(2) ?? '0.00'}', style: const TextStyle(color: Color(0xFFD97706), fontSize: 18, fontWeight: FontWeight.bold)),
                  ]),
                ),
                const SizedBox(height: 16),
                Expanded(child: ListView.builder(
                  itemCount: (_fees!['dues'] as List?)?.length ?? 0,
                  itemBuilder: (ctx, i) {
                    final due = (_fees!['dues'] as List)[i];
                    return Card(
                      color: const Color(0xFF111827),
                      margin: const EdgeInsets.only(bottom: 8),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      child: ListTile(
                        title: Text(due['fee_type'] ?? '', style: const TextStyle(color: Colors.white, fontSize: 14)),
                        subtitle: due['due_date'] != null ? Text('Due: ${due['due_date']}', style: const TextStyle(color: Colors.grey, fontSize: 12)) : null,
                        trailing: Text('₹${due['total']?.toStringAsFixed(0)}', style: const TextStyle(color: Color(0xFFD97706), fontWeight: FontWeight.bold)),
                      ),
                    );
                  },
                )),
              ]),
            ),
    );
  }
}

class ParentBusPage extends ConsumerStatefulWidget {
  const ParentBusPage({super.key});
  @override
  ConsumerState<ParentBusPage> createState() => _ParentBusPageState();
}

class _ParentBusPageState extends ConsumerState<ParentBusPage> {
  List<dynamic> _buses = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final api = ref.read(apiServiceProvider);
      final res = await api._dio.get('/bus/routes');
      setState(() { _buses = res.data as List; _loading = false; });
    } catch (_) { setState(() => _loading = false); }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Bus Tracking', style: TextStyle(fontWeight: FontWeight.bold))),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _buses.isEmpty
          ? const Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
              Icon(Icons.directions_bus, color: Colors.grey, size: 48),
              SizedBox(height: 12),
              Text('No buses assigned', style: TextStyle(color: Colors.grey)),
            ]))
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _buses.length,
              itemBuilder: (ctx, i) {
                final bus = _buses[i] as Map<String, dynamic>;
                final isOnline = bus['is_online'] == true;
                return Card(
                  color: const Color(0xFF111827),
                  margin: const EdgeInsets.only(bottom: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: BorderSide(color: isOnline ? const Color(0xFF059669).withOpacity(0.3) : const Color(0xFF374151))),
                  child: ListTile(
                    contentPadding: const EdgeInsets.all(16),
                    leading: Container(
                      width: 48, height: 48,
                      decoration: BoxDecoration(color: const Color(0xFF4F46E5).withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
                      child: const Icon(Icons.directions_bus, color: Color(0xFF4F46E5)),
                    ),
                    title: Text(bus['route_name'] ?? 'Bus', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      const SizedBox(height: 4),
                      Text(bus['vehicle_number'] ?? '', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                      Text('Driver: ${bus['driver_name'] ?? ''}', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                    ]),
                    trailing: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                      Container(width: 8, height: 8, decoration: BoxDecoration(color: isOnline ? Colors.green : Colors.red, shape: BoxShape.circle)),
                      const SizedBox(height: 4),
                      Text(isOnline ? 'Live' : 'Offline', style: TextStyle(color: isOnline ? Colors.green : Colors.red, fontSize: 11)),
                    ]),
                    onTap: isOnline ? () {} : null,
                  ),
                );
              },
            ),
    );
  }
}

class ParentNoticesPage extends StatelessWidget {
  const ParentNoticesPage({super.key});
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Notices', style: TextStyle(fontWeight: FontWeight.bold))),
      body: const Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(Icons.notifications_none, color: Colors.grey, size: 48),
        SizedBox(height: 12),
        Text('No notices', style: TextStyle(color: Colors.grey)),
      ])),
    );
  }
}
