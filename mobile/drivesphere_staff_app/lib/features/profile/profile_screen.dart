import 'package:flutter/material.dart';

import '../../services/staff_api_service.dart';
import '../../widgets/staff_scaffold.dart';

class ProfileScreen extends StatefulWidget {
  final bool showBackButton;

  const ProfileScreen({super.key, this.showBackButton = true});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _api = StaffApiService();

  String _name = '';
  String _email = '';
  String _role = '';
  String _branch = '';
  String _company = '';
  String _logoUrl = '';
  bool _loading = true;
  String _error = '';

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
        _name = payload.profile.fullName;
        _email = payload.profile.email;
        _role = payload.profile.roleCode;
        _branch = payload.activeBranch?.name ?? 'N/A';
        _company = payload.companyName.isEmpty ? 'DriveSphere' : payload.companyName;
        _logoUrl = payload.companyLogoUrl;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString().replaceFirst('Exception: ', '');
      });
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Widget _avatar() {
    if (_logoUrl.isNotEmpty) {
      return CircleAvatar(
        radius: 38,
        backgroundColor: Colors.white,
        backgroundImage: NetworkImage(_logoUrl),
      );
    }
    return const CircleAvatar(
      radius: 38,
      backgroundColor: Color(0xFF1F4E8C),
      child: Icon(Icons.person_rounded, size: 42, color: Colors.white),
    );
  }

  Widget _infoRow({
    required IconData icon,
    required String label,
    required String value,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0xF7FFFFFF),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFDDE5F2)),
      ),
      child: Row(
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: const Color(0x1A1F4E8C),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: const Color(0xFF1F4E8C), size: 18),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    fontSize: 12,
                    color: Color(0xFF7A879E),
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value.isEmpty ? '-' : value,
                  style: const TextStyle(
                    fontSize: 16,
                    color: Color(0xFF1F2A44),
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return StaffScaffold(
      title: 'Profile',
      showBackButton: widget.showBackButton,
      actions: [
        IconButton(
          onPressed: _loading ? null : _load,
          icon: const Icon(Icons.refresh_rounded),
          tooltip: 'Refresh',
        ),
      ],
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error.isNotEmpty
              ? Center(
                  child: Text(
                    _error,
                    style: const TextStyle(color: Color(0xFFB93830)),
                  ),
                )
              : SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFF1F4E8C), Color(0xFF2A6BC9)],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: const [
                            BoxShadow(
                              color: Color(0x331F4E8C),
                              blurRadius: 16,
                              offset: Offset(0, 6),
                            ),
                          ],
                        ),
                        child: Row(
                          children: [
                            _avatar(),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    _name.isEmpty ? 'Staff User' : _name,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 20,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    _email,
                                    style: const TextStyle(
                                      color: Color(0xD9FFFFFF),
                                      fontSize: 14,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 10,
                                      vertical: 4,
                                    ),
                                    decoration: BoxDecoration(
                                      color: const Color(0x26FFFFFF),
                                      borderRadius: BorderRadius.circular(999),
                                      border: Border.all(
                                        color: const Color(0x33FFFFFF),
                                      ),
                                    ),
                                    child: Text(
                                      _role,
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 14),
                      _infoRow(
                        icon: Icons.business_rounded,
                        label: 'Company',
                        value: _company,
                      ),
                      _infoRow(
                        icon: Icons.account_tree_outlined,
                        label: 'Active Branch',
                        value: _branch,
                      ),
                      _infoRow(
                        icon: Icons.alternate_email_rounded,
                        label: 'Email',
                        value: _email,
                      ),
                      _infoRow(
                        icon: Icons.badge_outlined,
                        label: 'Role',
                        value: _role,
                      ),
                    ],
                  ),
                ),
    );
  }
}
