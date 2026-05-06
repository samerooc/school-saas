// lib/screens/teacher/teacher_shell.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../services/auth_provider.dart';
import '../../services/api_service.dart';

class TeacherShell extends ConsumerStatefulWidget {
  const TeacherShell({super.key});
  @override
  ConsumerState<TeacherShell> createState() => _TeacherShellState();
}

class _TeacherShellState extends ConsumerState<TeacherShell> {
  int _index = 0;
  @override
  Widget build(BuildContext context) {
    final pages = [const TeacherHomePage(), const TeacherAttendancePage()];
    return Scaffold(
      body: pages[_index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        backgroundColor: const Color(0xFF111827),
        indicatorColor: const Color(0xFF7C3AED).withOpacity(0.2),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.checklist), selectedIcon: Icon(Icons.checklist), label: 'Attendance'),
        ],
      ),
    );
  }
}

class TeacherHomePage extends ConsumerWidget {
  const TeacherHomePage({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Teacher Portal', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF111827),
        actions: [IconButton(icon: const Icon(Icons.logout), onPressed: () => ref.read(authProvider.notifier).logout())],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Hello, ${auth.fullName?.split(' ').first ?? 'Teacher'}! 👋',
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(height: 20),
          Card(
            color: const Color(0xFF111827),
            child: ListTile(
              leading: const Icon(Icons.checklist, color: Color(0xFF7C3AED)),
              title: const Text('Mark Attendance', style: TextStyle(color: Colors.white)),
              trailing: const Icon(Icons.arrow_forward_ios, size: 14, color: Colors.grey),
            ),
          ),
        ]),
      ),
    );
  }
}

class TeacherAttendancePage extends ConsumerStatefulWidget {
  const TeacherAttendancePage({super.key});
  @override
  ConsumerState<TeacherAttendancePage> createState() => _TeacherAttendancePageState();
}

class _TeacherAttendancePageState extends ConsumerState<TeacherAttendancePage> {
  List<dynamic> _classes = [];
  String? _selectedClassId;
  List<Map<String, dynamic>> _students = [];
  Map<String, String> _statuses = {};
  bool _loading = false;
  bool _submitted = false;

  @override
  void initState() { super.initState(); _loadClasses(); }

  Future<void> _loadClasses() async {
    final api = ref.read(apiServiceProvider);
    try {
      final data = await api.getClasses();
      setState(() => _classes = data);
    } catch (_) {}
  }

  Future<void> _loadStudents(String classId) async {
    setState(() { _loading = true; _students = []; _statuses = {}; });
    try {
      final api = ref.read(apiServiceProvider);
      final data = await api.getStudents(classId: classId);
      final items = (data['items'] as List).cast<Map<String, dynamic>>();
      final statuses = <String, String>{};
      for (final s in items) { statuses[s['id']] = 'present'; }
      setState(() { _students = items; _statuses = statuses; _loading = false; });
    } catch (_) { setState(() => _loading = false); }
  }

  Future<void> _submit() async {
    if (_selectedClassId == null) return;
    final api = ref.read(apiServiceProvider);
    try {
      await api.markAttendance(
        classId: _selectedClassId!,
        date: DateTime.now().toIso8601String().split('T')[0],
        entries: _statuses.entries.map((e) => {'student_id': e.key, 'status': e.value}).toList(),
      );
      setState(() => _submitted = true);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_submitted) return Scaffold(
      body: Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        const Icon(Icons.check_circle, color: Colors.green, size: 64),
        const SizedBox(height: 16),
        const Text('Attendance Submitted!', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        ElevatedButton(onPressed: () => setState(() { _submitted = false; _selectedClassId = null; _students = []; }), child: const Text('Mark Another')),
      ])),
    );

    return Scaffold(
      appBar: AppBar(title: const Text('Mark Attendance'), backgroundColor: const Color(0xFF111827)),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          DropdownButtonFormField<String>(
            value: _selectedClassId,
            decoration: InputDecoration(labelText: 'Select Class', filled: true, fillColor: const Color(0xFF111827), border: OutlineInputBorder(borderRadius: BorderRadius.circular(12))),
            items: _classes.map<DropdownMenuItem<String>>((c) => DropdownMenuItem(value: c['id'] as String, child: Text('${c['name']}${c['section'] != null ? ' - ${c['section']}' : ''}', style: const TextStyle(color: Colors.white)))).toList(),
            onChanged: (v) { setState(() => _selectedClassId = v); if (v != null) _loadStudents(v); },
            dropdownColor: const Color(0xFF111827),
            style: const TextStyle(color: Colors.white),
          ),
          const SizedBox(height: 16),
          if (_loading) const CircularProgressIndicator()
          else if (_students.isNotEmpty) ...[
            Row(children: [
              TextButton(onPressed: () => setState(() => _statuses.updateAll((k, v) => 'present')), child: const Text('All Present', style: TextStyle(color: Colors.green))),
              TextButton(onPressed: () => setState(() => _statuses.updateAll((k, v) => 'absent')), child: const Text('All Absent', style: TextStyle(color: Colors.red))),
            ]),
            Expanded(child: ListView.builder(
              itemCount: _students.length,
              itemBuilder: (ctx, i) {
                final s = _students[i];
                final status = _statuses[s['id']] ?? 'present';
                return GestureDetector(
                  onTap: () => setState(() => _statuses[s['id']] = status == 'present' ? 'absent' : status == 'absent' ? 'late' : 'present'),
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: status == 'present' ? Colors.green.withOpacity(0.1) : status == 'absent' ? Colors.red.withOpacity(0.1) : Colors.orange.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: status == 'present' ? Colors.green.withOpacity(0.3) : status == 'absent' ? Colors.red.withOpacity(0.3) : Colors.orange.withOpacity(0.3)),
                    ),
                    child: Row(children: [
                      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(s['full_name'] ?? '', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500)),
                        if (s['roll_number'] != null) Text('Roll: ${s['roll_number']}', style: const TextStyle(color: Colors.grey, fontSize: 11)),
                      ])),
                      Icon(status == 'present' ? Icons.check_circle : status == 'absent' ? Icons.cancel : Icons.access_time,
                        color: status == 'present' ? Colors.green : status == 'absent' ? Colors.red : Colors.orange),
                    ]),
                  ),
                );
              },
            )),
            ElevatedButton(
              onPressed: _submit,
              style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50), backgroundColor: const Color(0xFF4F46E5), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))),
              child: const Text('Submit Attendance', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            ),
          ],
        ]),
      ),
    );
  }
}
