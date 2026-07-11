import 'package:flutter/material.dart';

import '../../core/models/branch_model.dart';
import '../../services/staff_api_service.dart';
import '../../widgets/empty_state_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/staff_scaffold.dart';

class BranchesScreen extends StatefulWidget {
  const BranchesScreen({super.key});

  @override
  State<BranchesScreen> createState() => _BranchesScreenState();
}

class _BranchesScreenState extends State<BranchesScreen> {
  final _api = StaffApiService();
  bool _loading = true;
  String _error = '';
  int? _activeBranchId;
  List<BranchModel> _items = const [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final payload = await _api.fetchBootstrap();
      if (!mounted) return;
      setState(() {
        _items = payload.branches;
        _activeBranchId = payload.activeBranch?.id;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return StaffScaffold(
      title: 'Branches',
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error.isNotEmpty
              ? Center(child: Text(_error))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(
                    children: [
                      SectionHeader(
                        title: 'Branch Directory',
                        subtitle: '${_items.length} branch(es)',
                        trailing: IconButton(
                          onPressed: _load,
                          icon: const Icon(Icons.refresh_rounded),
                        ),
                      ),
                      const SizedBox(height: 8),
                      if (_items.isEmpty)
                        const EmptyStateCard(
                          icon: Icons.apartment_outlined,
                          title: 'No Branches Found',
                          message: 'Branches configured in web settings will appear here.',
                        )
                      else
                        ..._items.map((branch) {
                          final isActive = _activeBranchId == branch.id;
                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
                            decoration: BoxDecoration(
                              color: const Color(0xF8FFFFFF),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(
                                color: isActive ? const Color(0xFF9DB7DC) : const Color(0xFFD8E2F0),
                              ),
                            ),
                            child: Row(
                              children: [
                                Container(
                                  width: 40,
                                  height: 40,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: const Color(0xFFEAF1FD),
                                    border: Border.all(color: const Color(0xFFD8E2F0)),
                                  ),
                                  child: const Icon(Icons.apartment_rounded, color: Color(0xFF234E87)),
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        branch.name,
                                        style: const TextStyle(
                                          fontWeight: FontWeight.w700,
                                          color: Color(0xFF1E3355),
                                        ),
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        branch.code,
                                        style: const TextStyle(
                                          color: Color(0xFF6A7390),
                                          fontSize: 13,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                if (isActive)
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFFEAF1FD),
                                      borderRadius: BorderRadius.circular(999),
                                      border: Border.all(color: const Color(0xFFBCD0EE)),
                                    ),
                                    child: const Text(
                                      'ACTIVE',
                                      style: TextStyle(
                                        fontWeight: FontWeight.w700,
                                        color: Color(0xFF234E87),
                                        fontSize: 11,
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                          );
                        }),
                    ],
                  ),
                ),
    );
  }
}
