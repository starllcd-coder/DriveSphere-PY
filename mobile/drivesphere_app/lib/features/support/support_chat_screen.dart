import 'package:flutter/material.dart';

import '../../models/support_message_model.dart';
import '../../services/api_service.dart';
import '../../widgets/app_error_state.dart';
import '../../widgets/app_skeleton.dart';

class SupportChatScreen extends StatefulWidget {
  const SupportChatScreen({super.key});

  @override
  State<SupportChatScreen> createState() => _SupportChatScreenState();
}

class _SupportChatScreenState extends State<SupportChatScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  bool _loading = true;
  bool _sending = false;
  bool _retrying = false;
  String? _error;
  List<SupportMessageModel> _messages = <SupportMessageModel>[];
  final Set<int> _pendingMessageIds = <int>{};

  @override
  void initState() {
    super.initState();
    _loadMessages();
  }

  Future<void> _loadMessages({
    bool showLoader = true,
    bool showRetrying = false,
  }) async {
    setState(() {
      if (showLoader) _loading = true;
      _retrying = showRetrying;
      _error = null;
    });
    try {
      final items = await _apiService.fetchSupportMessages();
      if (!mounted) return;
      setState(() => _messages = items);
      _scrollToBottom();
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = 'Failed to load chat messages.');
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
          _retrying = false;
        });
      }
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOut,
      );
    });
  }

  Future<void> _sendMessage() async {
    final message = _messageController.text.trim();
    if (message.isEmpty || _sending) return;
    _messageController.clear();

    final tempId = -DateTime.now().millisecondsSinceEpoch;
    final optimistic = SupportMessageModel(
      id: tempId,
      sender: 'customer',
      createdAt: DateTime.now().toIso8601String(),
      message: message,
    );

    setState(() {
      _sending = true;
      _messages = [..._messages, optimistic];
      _pendingMessageIds.add(tempId);
    });
    _scrollToBottom();

    try {
      await _apiService.sendSupportMessage(message);
      await _loadMessages(showLoader: false);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _messages.removeWhere((m) => m.id == tempId);
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Unable to send message. Please try again.'),
          backgroundColor: Color(0xFFD14848),
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _sending = false;
          _pendingMessageIds.remove(tempId);
        });
      }
    }
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        title: const Text('Support Chat'),
        actions: [
          IconButton(
            onPressed: _loading ? null : () => _loadMessages(showLoader: false),
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _loading
                ? const AppSkeletonList(itemHeight: 62, count: 8)
                : _error != null
                    ? AppErrorState(
                        title: 'Chat unavailable',
                        subtitle: _error!,
                        onRetry: () => _loadMessages(
                          showLoader: false,
                          showRetrying: true,
                        ),
                        isRetrying: _retrying,
                      )
                    : _messages.isEmpty
                        ? const Center(child: Text('No messages yet'))
                        : ListView.builder(
                            controller: _scrollController,
                            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                            itemCount: _messages.length,
                            itemBuilder: (context, index) {
                              final message = _messages[index];
                              final isCustomer = message.sender == 'customer';
                              final pending =
                                  _pendingMessageIds.contains(message.id);
                              return Align(
                                alignment: isCustomer
                                    ? Alignment.centerRight
                                    : Alignment.centerLeft,
                                child: Opacity(
                                  opacity: pending ? 0.65 : 1,
                                  child: Container(
                                    margin: const EdgeInsets.only(bottom: 10),
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: isCustomer
                                          ? const Color(0xFF234E8C)
                                          : Colors.white,
                                      borderRadius: BorderRadius.circular(16),
                                      boxShadow: [
                                        BoxShadow(
                                          color: const Color(0xFFB7C0D1)
                                              .withAlpha(41),
                                          blurRadius: 10,
                                          offset: const Offset(0, 6),
                                        ),
                                      ],
                                    ),
                                    child: Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Flexible(
                                          child: Text(
                                            message.message,
                                            style: TextStyle(
                                              color: isCustomer
                                                  ? Colors.white
                                                  : const Color(0xFF162E60),
                                              fontSize: 13.5,
                                            ),
                                          ),
                                        ),
                                        if (pending) ...[
                                          const SizedBox(width: 8),
                                          const SizedBox(
                                            width: 12,
                                            height: 12,
                                            child: CircularProgressIndicator(
                                              strokeWidth: 2,
                                              color: Colors.white,
                                            ),
                                          ),
                                        ],
                                      ],
                                    ),
                                  ),
                                ),
                              );
                            },
                          ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _messageController,
                      enabled: !_sending,
                      decoration: InputDecoration(
                        hintText: 'Type your message',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  SizedBox(
                    height: 48,
                    width: 48,
                    child: ElevatedButton(
                      onPressed: _sending ? null : _sendMessage,
                      child: _sending
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Icon(Icons.send_rounded),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
