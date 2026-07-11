import 'package:flutter/material.dart';

import '../../core/routes/app_routes.dart';
import '../../services/staff_api_service.dart';
import '../../widgets/brand_background.dart';
import '../../widgets/glass_panel.dart';

class BranchSelectorScreen extends StatefulWidget {
  final StaffBootstrapPayload payload;

  const BranchSelectorScreen({super.key, required this.payload});

  @override
  State<BranchSelectorScreen> createState() => _BranchSelectorScreenState();
}

class _BranchSelectorScreenState extends State<BranchSelectorScreen> {
  final _api = StaffApiService();
  bool _loading = false;

  Future<void> _selectBranch(int branchId) async {
    setState(() => _loading = true);
    try {
      final payload = await _api.fetchBootstrap(branchId: branchId);
      if (!mounted) return;
      Navigator.pushReplacementNamed(context, AppRoutes.shell,
          arguments: payload);
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final branches = widget.payload.branches;

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(title: const Text('Select Branch')),
      body: BrandBackground(
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: GlassPanel(
              child: ListView.separated(
                itemCount: branches.length,
                separatorBuilder: (_, __) => const SizedBox(height: 10),
                itemBuilder: (context, index) {
                  final branch = branches[index];
                  return ListTile(
                    enabled: !_loading,
                    tileColor: const Color(0xCCFFFFFF),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                      side: const BorderSide(color: Color(0x55FFFFFF)),
                    ),
                    title: Text(branch.name),
                    subtitle: Text(branch.code),
                    trailing:
                        const Icon(Icons.arrow_forward_ios_rounded, size: 18),
                    onTap: () => _selectBranch(branch.id),
                  );
                },
              ),
            ),
          ),
        ),
      ),
    );
  }
}
