import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'support_chat_screen.dart';

class SupportScreen extends StatelessWidget {
  const SupportScreen({super.key});

  Future<void> _openWhatsApp() async {
    final url = Uri.parse('https://wa.me/96890000000');
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        title: const Text('Customer Support'),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          _section(
            title: 'Contact channels',
            children: [
              ListTile(
                leading: const Icon(Icons.chat_outlined),
                title: const Text('WhatsApp support'),
                subtitle: const Text('Chat directly with DriveSphere support'),
                onTap: _openWhatsApp,
              ),
              const Divider(height: 8),
              ListTile(
                leading: const Icon(Icons.support_agent_rounded),
                title: const Text('In-app messaging'),
                subtitle: const Text('Start a conversation with support'),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const SupportChatScreen(),
                    ),
                  );
                },
              ),
            ],
          ),
          const SizedBox(height: 16),
          _section(
            title: 'Help Center',
            children: const [
              ListTile(
                leading: Icon(Icons.help_outline_rounded),
                title: Text('How to upload documents?'),
                subtitle: Text('Go to Profile > My Documents and upload once.'),
              ),
              Divider(height: 8),
              ListTile(
                leading: Icon(Icons.help_outline_rounded),
                title: Text('How do refunds work?'),
                subtitle:
                    Text('Refunds follow each company cancellation policy.'),
              ),
              Divider(height: 8),
              ListTile(
                leading: Icon(Icons.help_outline_rounded),
                title: Text('Can I book multiple vehicles?'),
                subtitle: Text('Yes, if availability allows.'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _section({required String title, required List<Widget> children}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 10),
          ...children,
        ],
      ),
    );
  }
}
