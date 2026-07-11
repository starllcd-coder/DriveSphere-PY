import 'package:flutter/material.dart';

import '../../services/staff_api_service.dart';
import '../../widgets/empty_state_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/staff_scaffold.dart';

class EmployeesScreen extends StatefulWidget {
  const EmployeesScreen({super.key});

  @override
  State<EmployeesScreen> createState() => _EmployeesScreenState();
}

class _EmployeesScreenState extends State<EmployeesScreen> {
  final _api = StaffApiService();
  List<Map<String, dynamic>> _rows = const [];
  bool _loading = true;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await _api.fetchEmployees();
      if (!mounted) return;
      setState(() => _rows = data);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return StaffScaffold(
      title: 'Employees',
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error.isNotEmpty
              ? Center(child: Text(_error))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(
                    children: [
                      SectionHeader(
                        title: 'Team Directory',
                        subtitle: '${_rows.length} employee(s)',
                        trailing: IconButton(
                          onPressed: _load,
                          icon: const Icon(Icons.refresh_rounded),
                        ),
                      ),
                      const SizedBox(height: 8),
                      if (_rows.isEmpty)
                        const EmptyStateCard(
                          icon: Icons.groups_outlined,
                          title: 'No Team Members Found',
                          message: 'Employees will appear here once available.',
                        )
                      else
                        ..._rows.map((item) {
                          final role = (item['role'] as Map?)?['code']?.toString() ?? 'N/A';
                          final fullName = item['full_name']?.toString().trim() ?? '';
                          final email = item['email']?.toString().trim() ?? '';
                          final displayName = fullName.isEmpty ? (email.isEmpty ? 'Employee' : email) : fullName;

                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
                            decoration: BoxDecoration(
                              color: const Color(0xF8FFFFFF),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: const Color(0xFFD8E2F0)),
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
                                  child: const Icon(Icons.person_outline_rounded, color: Color(0xFF234E87)),
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        displayName,
                                        style: const TextStyle(
                                          fontWeight: FontWeight.w700,
                                          color: Color(0xFF1E3355),
                                        ),
                                      ),
                                      if (email.isNotEmpty) ...[
                                        const SizedBox(height: 2),
                                        Text(
                                          email,
                                          style: const TextStyle(
                                            color: Color(0xFF6A7390),
                                            fontSize: 13,
                                          ),
                                        ),
                                      ],
                                    ],
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFF1F5FC),
                                    borderRadius: BorderRadius.circular(999),
                                    border: Border.all(color: const Color(0xFFDFE7F5)),
                                  ),
                                  child: Text(
                                    role,
                                    style: const TextStyle(
                                      fontSize: 12,
                                      color: Color(0xFF465271),
                                      fontWeight: FontWeight.w700,
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
