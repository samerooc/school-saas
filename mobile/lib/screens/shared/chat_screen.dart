// lib/screens/shared/chat_screen.dart
import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../services/api_service.dart';
import '../../services/auth_provider.dart';

class ChatScreen extends ConsumerStatefulWidget {
  final String partnerId;
  final String partnerName;
  final String partnerRole;
  const ChatScreen({
    super.key,
    required this.partnerId,
    required this.partnerName,
    required this.partnerRole,
  });

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _textCtrl   = TextEditingController();
  final _scrollCtrl = ScrollController();
  final List<Map<String, dynamic>> _messages = [];
  WebSocketChannel? _channel;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadHistory();
    _connectWS();
  }

  @override
  void dispose() {
    _textCtrl.dispose();
    _scrollCtrl.dispose();
    _channel?.sink.close();
    super.dispose();
  }

  Future<void> _loadHistory() async {
    try {
      final api = ref.read(apiServiceProvider);
      final res = await api._dio.get('/chat/messages/${widget.partnerId}');
      final data = res.data as Map<String, dynamic>;
      setState(() {
        _messages.addAll((data['messages'] as List).cast<Map<String, dynamic>>());
        _loading = false;
      });
      _scrollToBottom();
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  void _connectWS() {
    final token = SecureTokenStorage.getAccessToken();
    // WebSocket connection for real-time
    // In production use actual WS URL
  }

  Future<void> _sendMessage() async {
    final text = _textCtrl.text.trim();
    if (text.isEmpty) return;
    _textCtrl.clear();

    final userId = await SecureTokenStorage.getUserId();
    final optimistic = {
      'id': 'tmp-${DateTime.now().millisecondsSinceEpoch}',
      'sender_id': userId,
      'receiver_id': widget.partnerId,
      'text': text,
      'created_at': DateTime.now().toIso8601String(),
    };
    setState(() => _messages.add(optimistic));
    _scrollToBottom();

    try {
      final api = ref.read(apiServiceProvider);
      await api._dio.post(
        '/chat/messages/${widget.partnerId}',
        queryParameters: {'text': text},
      );
    } catch (_) {}
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(children: [
          CircleAvatar(
            radius: 16,
            backgroundColor: const Color(0xFF4F46E5),
            child: Text(widget.partnerName.substring(0, 1),
              style: const TextStyle(color: Colors.white, fontSize: 13)),
          ),
          const SizedBox(width: 10),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(widget.partnerName, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
            Text(widget.partnerRole.toUpperCase(),
              style: const TextStyle(fontSize: 10, color: Colors.grey)),
          ]),
        ]),
        backgroundColor: const Color(0xFF111827),
      ),
      body: Column(
        children: [
          // Messages
          Expanded(
            child: _loading
              ? const Center(child: CircularProgressIndicator())
              : ListView.builder(
                  controller: _scrollCtrl,
                  padding: const EdgeInsets.all(16),
                  itemCount: _messages.length,
                  itemBuilder: (ctx, i) {
                    final msg = _messages[i];
                    final isMe = msg['sender_id'] == ref.read(authProvider).userId;
                    return _MessageBubble(msg: msg, isMe: isMe);
                  },
                ),
          ),

          // Input
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: const BoxDecoration(
              color: Color(0xFF111827),
              border: Border(top: BorderSide(color: Color(0xFF374151))),
            ),
            child: Row(children: [
              Expanded(
                child: TextField(
                  controller: _textCtrl,
                  style: const TextStyle(color: Colors.white),
                  maxLength: 1000,
                  maxLines: null,
                  decoration: InputDecoration(
                    hintText: 'Type a message...',
                    hintStyle: const TextStyle(color: Colors.grey),
                    counterText: '',
                    filled: true,
                    fillColor: const Color(0xFF1F2937),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(20),
                      borderSide: BorderSide.none,
                    ),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  ),
                  onSubmitted: (_) => _sendMessage(),
                ),
              ),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: _sendMessage,
                child: Container(
                  width: 40, height: 40,
                  decoration: BoxDecoration(
                    color: const Color(0xFF4F46E5),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Icon(Icons.send_rounded, color: Colors.white, size: 18),
                ),
              ),
            ]),
          ),
        ],
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final Map<String, dynamic> msg;
  final bool isMe;
  const _MessageBubble({required this.msg, required this.isMe});

  @override
  Widget build(BuildContext context) {
    final time = DateTime.tryParse(msg['created_at'] ?? '');
    final timeStr = time != null
        ? '${time.hour.toString().padLeft(2,'0')}:${time.minute.toString().padLeft(2,'0')}'
        : '';

    return Align(
      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.72),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: isMe ? const Color(0xFF4F46E5) : const Color(0xFF1F2937),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isMe ? 16 : 4),
            bottomRight: Radius.circular(isMe ? 4 : 16),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(msg['text'] ?? '',
              style: TextStyle(
                color: isMe ? Colors.white : Colors.white70,
                fontSize: 14, height: 1.4)),
            const SizedBox(height: 4),
            Text(timeStr,
              style: TextStyle(
                color: isMe ? Colors.white54 : Colors.grey,
                fontSize: 10)),
          ],
        ),
      ),
    );
  }
}
