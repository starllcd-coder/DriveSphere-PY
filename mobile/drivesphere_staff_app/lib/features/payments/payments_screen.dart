import 'package:flutter/material.dart';

import '../../core/formatters/currency_formatter.dart';
import '../../services/staff_api_service.dart';
import '../../widgets/empty_state_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/staff_scaffold.dart';

class PaymentsScreen extends StatefulWidget {
  const PaymentsScreen({super.key});

  @override
  State<PaymentsScreen> createState() => _PaymentsScreenState();
}

class _PaymentsScreenState extends State<PaymentsScreen> {
  final _api = StaffApiService();
  final _searchController = TextEditingController();
  List<Map<String, dynamic>> _rows = const [];
  Set<String> _permissions = const <String>{};
  Set<int> _pendingIds = const <int>{};
  int _pendingCount = 0;
  bool _loading = true;
  String _error = '';
  String _statusFilter = 'ALL';

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

  Future<void> _load({String query = ''}) async {
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final results = await Future.wait([
        _api.getBootstrapCachedOrFetch(),
        _api.fetchPayments(query: query),
        _api.pendingPaymentIds(),
        _api.pendingActionsForPrefix('/internal/payments/'),
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

  bool _isPositiveAmount(String value) {
    final parsed = double.tryParse(value.trim());
    return parsed != null && parsed > 0;
  }

  List<Map<String, dynamic>> _filteredRows() {
    if (_statusFilter == 'ALL') return _rows;
    return _rows
        .where((item) => (item['status']?.toString() ?? '') == _statusFilter)
        .toList();
  }

  Future<void> _showCreatePaymentDialog() async {
    if (!_permissions.contains('payments.create')) return;
    final bookingIdController = TextEditingController();
    final amountController = TextEditingController();
    final notesController = TextEditingController();
    String method = 'CASH';
    String formError = '';

    await showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setStateDialog) {
            return AlertDialog(
              title: const Text('Collect Payment'),
              content: SingleChildScrollView(
                child: Column(
                  children: [
                    TextField(
                      controller: bookingIdController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(labelText: 'Booking ID'),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: amountController,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      decoration: const InputDecoration(labelText: 'Amount'),
                    ),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<String>(
                      initialValue: method,
                      decoration: const InputDecoration(labelText: 'Method'),
                      items: const [
                        DropdownMenuItem(value: 'CASH', child: Text('Cash')),
                        DropdownMenuItem(value: 'CARD', child: Text('Card')),
                        DropdownMenuItem(value: 'BANK_TRANSFER', child: Text('Bank Transfer')),
                        DropdownMenuItem(value: 'OTHER', child: Text('Other')),
                      ],
                      onChanged: (value) {
                        if (value == null) return;
                        setStateDialog(() => method = value);
                      },
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: notesController,
                      decoration: const InputDecoration(labelText: 'Notes'),
                    ),
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
                    final bookingId = int.tryParse(bookingIdController.text.trim()) ?? 0;
                    final amount = amountController.text.trim();
                    if (bookingId <= 0) {
                      setStateDialog(() => formError = 'Booking ID must be a positive number.');
                      return;
                    }
                    if (!_isPositiveAmount(amount)) {
                      setStateDialog(() => formError = 'Amount must be greater than zero.');
                      return;
                    }
                    try {
                      final result = await _api.createPayment(
                        bookingId: bookingId,
                        amount: amount,
                        method: method,
                        notes: notesController.text.trim(),
                      );
                      if (!mounted) return;
                      if (!dialogContext.mounted) return;
                      Navigator.pop(dialogContext);
                      await _load(query: _searchController.text.trim());
                      _showWriteResult(
                        queued: result['queued'] == true,
                        successMessage: 'Payment saved.',
                      );
                    } catch (e) {
                      setStateDialog(() => formError = e.toString().replaceFirst('Exception: ', ''));
                    }
                  },
                  child: const Text('Save'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Future<void> _showRefundDialog(int paymentId) async {
    if (!(_permissions.contains('payments.refund') || _permissions.contains('payments.manage'))) {
      return;
    }
    final amountController = TextEditingController();
    final notesController = TextEditingController();
    String method = 'CASH';
    String formError = '';

    await showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setStateDialog) {
            return AlertDialog(
              title: Text('Refund Payment #$paymentId'),
              content: SingleChildScrollView(
                child: Column(
                  children: [
                    TextField(
                      controller: amountController,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      decoration: const InputDecoration(labelText: 'Refund Amount'),
                    ),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<String>(
                      initialValue: method,
                      decoration: const InputDecoration(labelText: 'Method'),
                      items: const [
                        DropdownMenuItem(value: 'CASH', child: Text('Cash')),
                        DropdownMenuItem(value: 'CARD', child: Text('Card')),
                        DropdownMenuItem(value: 'BANK_TRANSFER', child: Text('Bank Transfer')),
                        DropdownMenuItem(value: 'OTHER', child: Text('Other')),
                      ],
                      onChanged: (value) {
                        if (value == null) return;
                        setStateDialog(() => method = value);
                      },
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: notesController,
                      decoration: const InputDecoration(labelText: 'Notes'),
                    ),
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
                    final amount = amountController.text.trim();
                    if (!_isPositiveAmount(amount)) {
                      setStateDialog(() => formError = 'Refund amount must be greater than zero.');
                      return;
                    }
                    try {
                      final result = await _api.createRefund(
                        paymentId: paymentId,
                        amount: amount,
                        method: method,
                        notes: notesController.text.trim(),
                      );
                      if (!mounted) return;
                      if (!dialogContext.mounted) return;
                      Navigator.pop(dialogContext);
                      await _load(query: _searchController.text.trim());
                      _showWriteResult(
                        queued: result['queued'] == true,
                        successMessage: 'Refund created.',
                      );
                    } catch (e) {
                      setStateDialog(() => formError = e.toString().replaceFirst('Exception: ', ''));
                    }
                  },
                  child: const Text('Refund'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final visibleRows = _filteredRows();
    return StaffScaffold(
      title: 'Payments',
      actions: [
        if (_permissions.contains('payments.create'))
          IconButton(
            onPressed: _showCreatePaymentDialog,
            icon: const Icon(Icons.add_card_rounded),
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
                        title: 'Transactions',
                        subtitle: '${visibleRows.length} payment record(s)',
                        trailing: IconButton(
                          onPressed: () => _load(query: _searchController.text.trim()),
                          icon: const Icon(Icons.refresh_rounded),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _searchController,
                              decoration: const InputDecoration(
                                hintText: 'Search by receipt, customer, note...',
                              ),
                              onSubmitted: (value) => _load(query: value),
                            ),
                          ),
                          const SizedBox(width: 8),
                          FilledButton.tonal(
                            onPressed: () =>
                                _load(query: _searchController.text.trim()),
                            child: const Text('Search'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Wrap(
                        spacing: 6,
                        children: [
                          for (final status in const ['ALL', 'PAID', 'VOID'])
                            ChoiceChip(
                              label: Text(status),
                              selected: _statusFilter == status,
                              onSelected: (_) =>
                                  setState(() => _statusFilter = status),
                            ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      if (_pendingCount > 0)
                        Container(
                          width: double.infinity,
                          margin: const EdgeInsets.only(bottom: 10),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 12, vertical: 8),
                          decoration: BoxDecoration(
                            color: const Color(0xFFE8F0FE),
                            borderRadius: BorderRadius.circular(10),
                            border:
                                Border.all(color: const Color(0xFFB7CCF7)),
                          ),
                          child:
                              Text('Pending payment actions to sync: $_pendingCount'),
                        ),
                      if (visibleRows.isEmpty)
                        const EmptyStateCard(
                          icon: Icons.account_balance_wallet_outlined,
                          title: 'No Payments Found',
                          message:
                              'Try another search/filter or collect a new payment.',
                        )
                      else
                        ...visibleRows.map((item) {
                          final paymentId = (item['id'] as num?)?.toInt() ?? 0;
                          final status = item['status']?.toString() ?? '';
                          final pending = _pendingIds.contains(paymentId);
                          final currencyCode = item['currency_code']
                                      ?.toString()
                                      .trim()
                                      .isNotEmpty ==
                                  true
                              ? item['currency_code'].toString().trim()
                              : 'OMR';
                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(14),
                              color: const Color(0xF8FFFFFF),
                              border:
                                  Border.all(color: const Color(0xFFD8E2F0)),
                            ),
                            child: ListTile(
                              title: Text(
                                item['receipt_number']?.toString() ?? 'Payment',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              subtitle: Text(
                                pending
                                    ? '${item['customer_name'] ?? ''} - ${item['method'] ?? ''} - $status\nPending Sync'
                                    : '${item['customer_name'] ?? ''} - ${item['method'] ?? ''} - $status',
                              ),
                              isThreeLine: pending,
                              trailing: Wrap(
                                crossAxisAlignment: WrapCrossAlignment.center,
                                spacing: 4,
                                children: [
                                  Text(
                                    formatCurrency(
                                      item['amount'],
                                      code: currencyCode,
                                      withCode: true,
                                    ),
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                  if (status == 'PAID' &&
                                      (_permissions.contains('payments.refund') ||
                                          _permissions.contains('payments.manage')))
                                    IconButton(
                                      onPressed: () => _showRefundDialog(paymentId),
                                      icon: const Icon(Icons.undo_rounded, size: 18),
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
}
