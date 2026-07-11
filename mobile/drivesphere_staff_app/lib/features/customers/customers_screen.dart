import 'package:flutter/material.dart';

import '../../services/staff_api_service.dart';
import '../../widgets/empty_state_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/staff_scaffold.dart';

class CustomersScreen extends StatefulWidget {
  const CustomersScreen({super.key});

  @override
  State<CustomersScreen> createState() => _CustomersScreenState();
}

class _CustomersScreenState extends State<CustomersScreen> {
  final _api = StaffApiService();
  final _searchController = TextEditingController();
  List<Map<String, dynamic>> _rows = const [];
  Set<String> _permissions = const <String>{};
  Set<int> _pendingIds = const <int>{};
  int _pendingCount = 0;
  bool _loading = true;
  String _error = '';

  void _showWriteResult({
    required bool queued,
    required String successMessage,
    String queuedMessage = 'No network. Action queued and will sync automatically.',
  }) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(queued ? queuedMessage : successMessage)),
    );
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _load({String query = ''}) async {
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final results = await Future.wait([
        _api.getBootstrapCachedOrFetch(),
        _api.fetchCustomers(query: query),
        _api.pendingCustomerIds(),
        _api.pendingActionsForPrefix('/internal/customers/'),
      ]);
      final bootstrap = results[0] as StaffBootstrapPayload;
      final data = results[1] as List<Map<String, dynamic>>;
      final pendingIds = results[2] as Set<int>;
      final pendingCount = results[3] as int;
      if (!mounted) return;
      setState(() {
        _rows = data;
        _permissions = bootstrap.profile.permissions.toSet();
        _pendingIds = pendingIds;
        _pendingCount = pendingCount;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _showCreateDialog() async {
    if (!_permissions.contains('customers.manage')) return;
    await _showEditCreateDialog();
  }

  Future<void> _showEditDialog(Map<String, dynamic> item) async {
    if (!_permissions.contains('customers.manage')) return;
    await _showEditCreateDialog(existing: item);
  }

  Future<void> _showEditCreateDialog({Map<String, dynamic>? existing}) async {
    final nameController = TextEditingController(text: existing?['name']?.toString() ?? '');
    final phoneController = TextEditingController(text: existing?['phone_number']?.toString() ?? '');
    final emailController = TextEditingController(text: existing?['email']?.toString() ?? '');
    final idNumberController = TextEditingController(text: existing?['id_number']?.toString() ?? '');
    String idType = existing?['id_type']?.toString() ?? 'ID';
    String formError = '';

    await showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setStateDialog) {
            return AlertDialog(
              title: Text(existing == null ? 'New Customer' : 'Edit Customer'),
              content: SingleChildScrollView(
                child: Column(
                  children: [
                    TextField(controller: nameController, decoration: const InputDecoration(labelText: 'Name')),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<String>(
                      initialValue: idType,
                      items: const [
                        DropdownMenuItem(value: 'ID', child: Text('ID')),
                        DropdownMenuItem(value: 'PASSPORT', child: Text('Passport')),
                        DropdownMenuItem(value: 'LICENSE', child: Text('License')),
                      ],
                      onChanged: (value) {
                        if (value == null) return;
                        setStateDialog(() => idType = value);
                      },
                      decoration: const InputDecoration(labelText: 'ID Type'),
                    ),
                    const SizedBox(height: 8),
                    TextField(controller: idNumberController, decoration: const InputDecoration(labelText: 'ID Number')),
                    const SizedBox(height: 8),
                    TextField(controller: phoneController, decoration: const InputDecoration(labelText: 'Phone')),
                    const SizedBox(height: 8),
                    TextField(controller: emailController, decoration: const InputDecoration(labelText: 'Email')),
                    if (formError.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text(formError, style: const TextStyle(color: Colors.red)),
                    ],
                  ],
                ),
              ),
              actions: [
                TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
                FilledButton(
                  onPressed: () async {
                    final name = nameController.text.trim();
                    final email = emailController.text.trim();
                    if (name.isEmpty) {
                      setStateDialog(() => formError = 'Name is required.');
                      return;
                    }
                    if (email.isNotEmpty && !email.contains('@')) {
                      setStateDialog(() => formError = 'Email format looks invalid.');
                      return;
                    }
                    try {
                      if (existing == null) {
                        final result = await _api.createCustomer(
                          name: name,
                          phoneNumber: phoneController.text.trim(),
                          email: email,
                          idType: idType,
                          idNumber: idNumberController.text.trim(),
                        );
                        _showWriteResult(
                          queued: result['queued'] == true,
                          successMessage: 'Customer created.',
                        );
                      } else {
                        final id = (existing['id'] as num?)?.toInt() ?? 0;
                        final result = await _api.updateCustomer(
                          customerId: id,
                          payload: {
                            'name': name,
                            'id_type': idType,
                            'id_number': idNumberController.text.trim(),
                            'phone_number': phoneController.text.trim(),
                            'email': email,
                          },
                        );
                        _showWriteResult(
                          queued: result['queued'] == true,
                          successMessage: 'Customer updated.',
                        );
                      }
                      if (!mounted) return;
                      if (!dialogContext.mounted) return;
                      Navigator.pop(dialogContext);
                      await _load(query: _searchController.text.trim());
                    } catch (e) {
                      setStateDialog(() => formError = e.toString().replaceFirst('Exception: ', ''));
                    }
                  },
                  child: Text(existing == null ? 'Create' : 'Save'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Future<void> _deleteCustomer(Map<String, dynamic> item) async {
    if (!_permissions.contains('customers.manage')) return;
    final id = (item['id'] as num?)?.toInt() ?? 0;
    final name = item['name']?.toString() ?? 'Customer';
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Customer'),
        content: Text('Delete $name?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('No')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete')),
        ],
      ),
    );
    if (confirmed != true) return;

    try {
      final queued = await _api.deleteCustomer(id);
      await _load(query: _searchController.text.trim());
      _showWriteResult(
        queued: queued,
        successMessage: 'Customer deleted.',
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return StaffScaffold(
      title: 'Customers',
      actions: [
        if (_permissions.contains('customers.manage'))
          IconButton(
            onPressed: _showCreateDialog,
            icon: const Icon(Icons.person_add_alt_1_rounded),
          ),
      ],
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error.isNotEmpty
              ? Center(child: Text(_error))
              : RefreshIndicator(
                  onRefresh: () => _load(query: _searchController.text.trim()),
                  child: ListView(
                    children: [
                      SectionHeader(
                        title: 'Customer Directory',
                        subtitle: '${_rows.length} customer(s)',
                        trailing: Wrap(
                          spacing: 8,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            if (_permissions.contains('customers.manage'))
                              FilledButton.tonalIcon(
                                onPressed: _showCreateDialog,
                                icon: const Icon(Icons.person_add_alt_1_rounded, size: 18),
                                label: const Text('New'),
                              ),
                            IconButton(
                              onPressed: () => _load(query: _searchController.text.trim()),
                              icon: const Icon(Icons.refresh_rounded),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _searchController,
                              decoration: const InputDecoration(
                                  hintText: 'Search by name, phone, email, ID...'),
                              onSubmitted: (value) => _load(query: value),
                            ),
                          ),
                          const SizedBox(width: 8),
                          FilledButton.tonal(
                            onPressed: () => _load(query: _searchController.text.trim()),
                            child: const Text('Search'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      if (_pendingCount > 0)
                        Container(
                          width: double.infinity,
                          margin: const EdgeInsets.only(bottom: 10),
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          decoration: BoxDecoration(
                            color: const Color(0xFFE8F0FE),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: const Color(0xFFB7CCF7)),
                          ),
                          child: Text('Pending customer actions to sync: $_pendingCount'),
                        ),
                      if (_rows.isEmpty)
                        const EmptyStateCard(
                          icon: Icons.group_outlined,
                          title: 'No Customers Found',
                          message: 'Create a customer or adjust your search to see records.',
                        )
                      else
                        ..._rows.map((item) {
                          final customerId = (item['id'] as num?)?.toInt() ?? 0;
                          final pending = _pendingIds.contains(customerId);
                          final name = item['name']?.toString().trim().isNotEmpty == true
                              ? item['name'].toString().trim()
                              : 'Customer';
                          final phone = item['phone_number']?.toString().trim() ?? '';
                          final email = item['email']?.toString().trim() ?? '';
                          final idType = item['id_type']?.toString().trim() ?? '';
                          final idNumber = item['id_number']?.toString().trim() ?? '';
                          final subtitle = <String>[
                            if (phone.isNotEmpty) phone,
                            if (email.isNotEmpty) email,
                          ].join('  |  ');

                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            decoration: BoxDecoration(
                              color: const Color(0xF8FFFFFF),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: const Color(0xFFD8E2F0)),
                            ),
                            child: Padding(
                              padding: const EdgeInsets.fromLTRB(12, 10, 8, 10),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Container(
                                    width: 42,
                                    height: 42,
                                    decoration: BoxDecoration(
                                      shape: BoxShape.circle,
                                      color: const Color(0xFFE9F0FB),
                                      border: Border.all(color: const Color(0xFFD8E2F0)),
                                    ),
                                    child: const Icon(
                                      Icons.person_outline_rounded,
                                      color: Color(0xFF234E87),
                                    ),
                                  ),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          children: [
                                            Expanded(
                                              child: Text(
                                                name,
                                                style: const TextStyle(
                                                  fontWeight: FontWeight.w700,
                                                  color: Color(0xFF1E3355),
                                                ),
                                              ),
                                            ),
                                            if (pending)
                                              Container(
                                                padding: const EdgeInsets.symmetric(
                                                  horizontal: 8,
                                                  vertical: 2,
                                                ),
                                                decoration: BoxDecoration(
                                                  color: const Color(0xFFFFF1D6),
                                                  borderRadius: BorderRadius.circular(999),
                                                  border: Border.all(
                                                    color: const Color(0xFFE5C98A),
                                                  ),
                                                ),
                                                child: const Text(
                                                  'Pending Sync',
                                                  style: TextStyle(
                                                    fontSize: 11,
                                                    color: Color(0xFF77540A),
                                                    fontWeight: FontWeight.w700,
                                                  ),
                                                ),
                                              ),
                                          ],
                                        ),
                                        const SizedBox(height: 4),
                                        if (subtitle.isNotEmpty)
                                          Text(
                                            subtitle,
                                            style: const TextStyle(
                                              color: Color(0xFF6A7390),
                                              fontSize: 13,
                                            ),
                                          ),
                                        const SizedBox(height: 6),
                                        if (idType.isNotEmpty || idNumber.isNotEmpty)
                                          Wrap(
                                            spacing: 6,
                                            runSpacing: 6,
                                            children: [
                                              _chip(idType.isEmpty ? 'ID' : idType),
                                              if (idNumber.isNotEmpty) _chip(idNumber),
                                            ],
                                          ),
                                      ],
                                    ),
                                  ),
                                  if (_permissions.contains('customers.manage'))
                                    PopupMenuButton<String>(
                                      onSelected: (value) {
                                        if (value == 'edit') {
                                          _showEditDialog(item);
                                        } else if (value == 'delete') {
                                          _deleteCustomer(item);
                                        }
                                      },
                                      itemBuilder: (context) => const [
                                        PopupMenuItem(value: 'edit', child: Text('Edit')),
                                        PopupMenuItem(value: 'delete', child: Text('Delete')),
                                      ],
                                    ),
                                ],
                              ),
                            ),
                          );
                        }),
                    ],
                  ),
                ),
    );
  }

  Widget _chip(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xFFF1F5FC),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: const Color(0xFFDFE7F5)),
      ),
      child: Text(
        text,
        style: const TextStyle(fontSize: 12, color: Color(0xFF465271)),
      ),
    );
  }
}
