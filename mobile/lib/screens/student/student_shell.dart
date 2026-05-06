// lib/screens/student/student_shell.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:youtube_player_flutter/youtube_player_flutter.dart';
import '../../services/api_service.dart';
import '../../services/auth_provider.dart';

// ── Student Shell (Bottom Nav) ────────────────────────────────────────────────

class StudentShell extends ConsumerStatefulWidget {
  const StudentShell({super.key});
  @override
  ConsumerState<StudentShell> createState() => _StudentShellState();
}

class _StudentShellState extends ConsumerState<StudentShell> {
  int _selectedIndex = 0;

  final _pages = const [
    StudentHomePage(),
    StudentVideosPage(),
    StudentAttendancePage(),
    StudentFeesPage(),
    StudentNoticesPage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (i) => setState(() => _selectedIndex = i),
        backgroundColor: const Color(0xFF111827),
        indicatorColor: const Color(0xFF4F46E5).withOpacity(0.2),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.play_circle_outline), selectedIcon: Icon(Icons.play_circle), label: 'Videos'),
          NavigationDestination(icon: Icon(Icons.calendar_today_outlined), selectedIcon: Icon(Icons.calendar_today), label: 'Attendance'),
          NavigationDestination(icon: Icon(Icons.payment_outlined), selectedIcon: Icon(Icons.payment), label: 'Fees'),
          NavigationDestination(icon: Icon(Icons.notifications_outlined), selectedIcon: Icon(Icons.notifications), label: 'Notices'),
        ],
      ),
    );
  }
}

// ── Home Page ─────────────────────────────────────────────────────────────────

class StudentHomePage extends ConsumerWidget {
  const StudentHomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('SchoolSaaS', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF111827),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout_rounded),
            onPressed: () => ref.read(authProvider.notifier).logout(),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Welcome, ${auth.fullName?.split(' ').first ?? 'Student'}! 👋',
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white)),
            const SizedBox(height: 4),
            const Text('Your learning dashboard', style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 20),
            Expanded(
              child: GridView.count(
                crossAxisCount: 2, crossAxisSpacing: 12, mainAxisSpacing: 12, childAspectRatio: 1.3,
                children: const [
                  _QuickCard(emoji: '🎬', label: 'My Videos', color: Color(0xFF4F46E5)),
                  _QuickCard(emoji: '📋', label: 'Attendance', color: Color(0xFF059669)),
                  _QuickCard(emoji: '💰', label: 'Fees', color: Color(0xFFD97706)),
                  _QuickCard(emoji: '📢', label: 'Notices', color: Color(0xFF7C3AED)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _QuickCard extends StatelessWidget {
  final String emoji, label;
  final Color color;
  const _QuickCard({required this.emoji, required this.label, required this.color});

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
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(emoji, style: const TextStyle(fontSize: 28)),
              const SizedBox(height: 6),
              Text(label, style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w500)),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Videos Page with YouTube Player ──────────────────────────────────────────

class StudentVideosPage extends ConsumerStatefulWidget {
  const StudentVideosPage({super.key});
  @override
  ConsumerState<StudentVideosPage> createState() => _StudentVideosPageState();
}

class _StudentVideosPageState extends ConsumerState<StudentVideosPage> {
  List<dynamic> _videos = [];
  Map<String, dynamic>? _selectedVideo;
  Map<String, dynamic>? _playerToken;
  YoutubePlayerController? _ytController;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadVideos();
  }

  @override
  void dispose() {
    _ytController?.dispose();
    super.dispose();
  }

  Future<void> _loadVideos() async {
    try {
      final api = ref.read(apiServiceProvider);
      final data = await api.getVideos();
      setState(() { _videos = data['items'] ?? []; _loading = false; });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  Future<void> _selectVideo(Map<String, dynamic> video) async {
    setState(() { _selectedVideo = video; _playerToken = null; });
    try {
      final api = ref.read(apiServiceProvider);
      final token = await api.getVideoPlayerToken(video['id']);
      setState(() => _playerToken = token);

      // Init YouTube player if available
      final ytEmbedUrl = token['youtube']?['embed_url'] as String?;
      if (ytEmbedUrl != null) {
        final ytId = YoutubePlayer.convertUrlToId(
          'https://www.youtube.com/watch?v=${token['youtube']['video_id']}'
        );
        if (ytId != null) {
          _ytController?.dispose();
          _ytController = YoutubePlayerController(
            initialVideoId: ytId,
            flags: const YoutubePlayerFlags(autoPlay: true, mute: false),
          );
        }
      }
    } catch (e) {
      // Token fetch failed — show error in player
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Videos', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF111827),
      ),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : Column(
          children: [
            // Player area
            if (_selectedVideo != null) _buildPlayer(),

            // Video list
            Expanded(
              child: ListView.builder(
                itemCount: _videos.length,
                itemBuilder: (ctx, i) {
                  final v = _videos[i] as Map<String, dynamic>;
                  final isSelected = _selectedVideo?['id'] == v['id'];
                  return ListTile(
                    selected: isSelected,
                    selectedTileColor: const Color(0xFF4F46E5).withOpacity(0.1),
                    leading: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: v['thumbnail_url'] != null
                        ? Image.network(v['thumbnail_url'], width: 60, height: 45, fit: BoxFit.cover,
                            errorBuilder: (_, __, ___) => const Icon(Icons.play_circle, color: Colors.grey))
                        : const Icon(Icons.play_circle, color: Colors.grey),
                    ),
                    title: Text(v['title'] ?? '', style: const TextStyle(color: Colors.white, fontSize: 13)),
                    subtitle: Text(
                      '${v['chapter_name'] ?? ''}${v['topic_name'] != null ? ' · ${v['topic_name']}' : ''}',
                      style: const TextStyle(color: Colors.grey, fontSize: 11),
                    ),
                    trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                      if (v['is_premium'] == true) const Icon(Icons.star, color: Colors.amber, size: 14),
                      if (v['has_youtube'] == true) const Icon(Icons.smart_display, color: Colors.red, size: 14),
                    ]),
                    onTap: () => _selectVideo(v),
                  );
                },
              ),
            ),
          ],
        ),
    );
  }

  Widget _buildPlayer() {
    if (_playerToken == null) {
      return Container(
        height: 220,
        color: Colors.black,
        child: const Center(child: CircularProgressIndicator()),
      );
    }

    // YouTube player
    if (_ytController != null) {
      return YoutubePlayerBuilder(
        player: YoutubePlayer(
          controller: _ytController!,
          showVideoProgressIndicator: true,
          progressColors: const ProgressBarColors(
            playedColor: Color(0xFF4F46E5),
            handleColor: Color(0xFF4F46E5),
          ),
        ),
        builder: (context, player) => player,
      );
    }

    // Fallback
    return Container(
      height: 220,
      color: Colors.black,
      child: const Center(
        child: Icon(Icons.play_circle, color: Colors.grey, size: 48),
      ),
    );
  }
}

// ── Placeholder screens ───────────────────────────────────────────────────────

class StudentAttendancePage extends ConsumerWidget {
  const StudentAttendancePage({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) => _PlaceholderPage(title: 'Attendance', icon: Icons.calendar_today);
}

class StudentFeesPage extends ConsumerWidget {
  const StudentFeesPage({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) => _PlaceholderPage(title: 'Fee Status', icon: Icons.payment);
}

class StudentNoticesPage extends ConsumerWidget {
  const StudentNoticesPage({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) => _PlaceholderPage(title: 'Notices', icon: Icons.notifications);
}

class _PlaceholderPage extends StatelessWidget {
  final String title;
  final IconData icon;
  const _PlaceholderPage({required this.title, required this.icon});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(title), backgroundColor: const Color(0xFF111827)),
    body: Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: Colors.grey, size: 48),
          const SizedBox(height: 12),
          Text(title, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          const Text('Coming in next update', style: TextStyle(color: Colors.grey)),
        ],
      ),
    ),
  );
}
