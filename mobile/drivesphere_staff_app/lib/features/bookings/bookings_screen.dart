import 'package:flutter/material.dart';

import '../../core/routes/app_routes.dart';
import '../../services/staff_api_service.dart';
import '../../widgets/empty_state_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/staff_scaffold.dart';

class BookingsScreen extends StatefulWidget {
  const BookingsScreen({super.key});

  @override
  State<BookingsScreen> createState() => _BookingsScreenState();
}

class _BookingsScreenState extends State<BookingsScreen> {
  final _api = StaffApiService();
  List<Map<String, dynamic>> _rows = const [];
  Set<String> _permissions = const <String>{};
  Set<int> _pendingIds = const <int>{};
  int _pendingCreateCount = 0;
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

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final results = await Future.wait([
        _api.fetchBootstrap(),
        _api.fetchBookings(),
        _api.pendingBookingIds(),
        _api.pendingActionsForPrefix('/internal/bookings/'),
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
        _pendingCreateCount = pendingCount;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _openBookingWizard() async {
    await Navigator.pushNamed(context, AppRoutes.bookingWizard);
    if (mounted) {
      await _load();
    }
  }

  List<Map<String, dynamic>> _filteredRows() {
    if (_statusFilter == 'ALL') return _rows;
    return _rows
        .where((item) => (item['status']?.toString() ?? '') == _statusFilter)
        .toList();
  }

  Widget _statusChip(String status) {
    final normalized = status.toUpperCase();
    Color bg;
    Color fg;
    switch (normalized) {
      case 'RETURNED':
      case 'CLOSED':
        bg = const Color(0x142D9B5C);
        fg = const Color(0xFF2D9B5C);
        break;
      case 'CHECKED_OUT':
      case 'CONFIRMED':
        bg = const Color(0x141F4E8C);
        fg = const Color(0xFF1F4E8C);
        break;
      case 'CANCELLED':
        bg = const Color(0x14B93830);
        fg = const Color(0xFFB93830);
        break;
      default:
        bg = const Color(0x14B57E1D);
        fg = const Color(0xFFB57E1D);
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        normalized,
        style: TextStyle(
          color: fg,
          fontSize: 11,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.2,
        ),
      ),
    );
  }

  Future<void> _showExtendDialog(int bookingId) async {
    final dateController = TextEditingController();
    await showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: Text('Extend Booking #$bookingId'),
          content: TextField(
            controller: dateController,
            decoration: const InputDecoration(labelText: 'New Return Date (YYYY-MM-DD)'),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            FilledButton(
              onPressed: () async {
                final queued = await _api.extendBooking(
                  bookingId: bookingId,
                  newReturnDate: dateController.text.trim(),
                );
                if (!mounted) return;
                if (!dialogContext.mounted) return;
                Navigator.pop(dialogContext);
                await _load();
                _showWriteResult(
                  queued: queued,
                  successMessage: 'Booking extended.',
                );
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _showCheckoutDialog(int bookingId) async {
    final odoController = TextEditingController();
    final fuelController = TextEditingController(text: '100');
    await showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: Text('Checkout Booking #$bookingId'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: odoController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Odometer Out (km)'),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: fuelController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Fuel Out (%)'),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            FilledButton(
              onPressed: () async {
                final queued = await _api.checkoutBooking(
                  bookingId: bookingId,
                  odometerOutKm: int.tryParse(odoController.text.trim()) ?? 0,
                  fuelOutPercent: int.tryParse(fuelController.text.trim()) ?? 100,
                );
                if (!mounted) return;
                if (!dialogContext.mounted) return;
                Navigator.pop(dialogContext);
                await _load();
                _showWriteResult(
                  queued: queued,
                  successMessage: 'Booking checked out.',
                );
              },
              child: const Text('Checkout'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _showReturnDialog(int bookingId) async {
    final odoController = TextEditingController();
    final fuelController = TextEditingController(text: '100');
    final fuelChargeController = TextEditingController(text: '0');
    final lateFeeController = TextEditingController(text: '0');
    final damageFeeController = TextEditingController(text: '0');
    final otherFeeController = TextEditingController(text: '0');
    final damageDetailsController = TextEditingController();

    await showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: Text('Return Booking #$bookingId'),
          content: SingleChildScrollView(
            child: Column(
              children: [
                TextField(
                  controller: odoController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Odometer In (km)'),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: fuelController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Fuel Return (%)'),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: fuelChargeController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: 'Fuel Charge'),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: lateFeeController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: 'Late Fee'),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: damageFeeController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: 'Damage Fee'),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: otherFeeController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: 'Other Fee'),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: damageDetailsController,
                  decoration: const InputDecoration(labelText: 'Damage Details'),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
            FilledButton(
              onPressed: () async {
                final result = await _api.returnBooking(
                  bookingId: bookingId,
                  odometerInKm: int.tryParse(odoController.text.trim()) ?? 0,
                  fuelReturnPercent: int.tryParse(fuelController.text.trim()) ?? 100,
                  fuelCharge: fuelChargeController.text.trim(),
                  lateFee: lateFeeController.text.trim(),
                  damageFee: damageFeeController.text.trim(),
                  otherFee: otherFeeController.text.trim(),
                  damageDetails: damageDetailsController.text.trim(),
                );
                if (!mounted) return;
                if (!dialogContext.mounted) return;
                Navigator.pop(dialogContext);
                await _load();
                _showWriteResult(
                  queued: result['queued'] == true,
                  successMessage: 'Booking returned.',
                );
              },
              child: const Text('Return'),
            ),
          ],
        );
      },
    );
  }

  Widget _buildActions(Map<String, dynamic> item) {
    final bookingId = (item['id'] as num?)?.toInt() ?? 0;
    final status = item['status']?.toString() ?? '';
    final canUpdate = _permissions.contains('bookings.update');
    final canExtend = _permissions.contains('bookings.extend');
    final canCheckout = _permissions.contains('bookings.checkout');
    final canReturn = _permissions.contains('bookings.return');
    final canDelete = _permissions.contains('bookings.delete');

    return Wrap(
      spacing: 4,
      runSpacing: 4,
      children: [
        if (status == 'UPCOMING' && canUpdate)
          OutlinedButton(
            onPressed: () async {
              final queued = await _api.activateBooking(bookingId);
              await _load();
              _showWriteResult(
                queued: queued,
                successMessage: 'Booking activated.',
              );
            },
            child: const Text('Activate'),
          ),
        if ((status == 'CONFIRMED' || status == 'UPCOMING' || status == 'CHECKED_OUT') && canExtend)
          OutlinedButton(
            onPressed: () => _showExtendDialog(bookingId),
            child: const Text('Extend'),
          ),
        if ((status == 'CONFIRMED' || status == 'UPCOMING') && canCheckout)
          OutlinedButton(
            onPressed: () => _showCheckoutDialog(bookingId),
            child: const Text('Checkout'),
          ),
        if ((status == 'CHECKED_OUT' || status == 'CONFIRMED' || status == 'UPCOMING') && canReturn)
          OutlinedButton(
            onPressed: () => _showReturnDialog(bookingId),
            child: const Text('Return'),
          ),
        if (status != 'RETURNED' && status != 'CLOSED' && status != 'CANCELLED' && canDelete)
          OutlinedButton(
            onPressed: () async {
              final queued = await _api.cancelBooking(bookingId);
              await _load();
              _showWriteResult(
                queued: queued,
                successMessage: 'Booking cancelled.',
              );
            },
            child: const Text('Cancel'),
          ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final visibleRows = _filteredRows();
    return StaffScaffold(
      title: 'Bookings',
      actions: [
        if (_permissions.contains('bookings.create'))
          IconButton(
            onPressed: _openBookingWizard,
            icon: const Icon(Icons.add_rounded),
          ),
      ],
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error.isNotEmpty
              ? Center(child: Text(_error))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(
                    children: [
                      SectionHeader(
                        title: 'Booking Queue',
                        subtitle: '${visibleRows.length} visible booking(s)',
                        trailing: FilledButton.tonalIcon(
                          onPressed: _openBookingWizard,
                          icon: const Icon(Icons.add_rounded, size: 18),
                          label: const Text('New'),
                        ),
                      ),
                      const SizedBox(height: 10),
                      SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          children: [
                            for (final status in const [
                              'ALL',
                              'CONFIRMED',
                              'CHECKED_OUT',
                              'RETURNED',
                              'UPCOMING',
                              'CANCELLED',
                            ])
                              Padding(
                                padding: const EdgeInsets.only(right: 6),
                                child: ChoiceChip(
                                  label: Text(status),
                                  selected: _statusFilter == status,
                                  onSelected: (_) =>
                                      setState(() => _statusFilter = status),
                                ),
                              ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 10),
                      if (_pendingCreateCount > 0)
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
                          child: Text(
                              'Pending booking actions to sync: $_pendingCreateCount'),
                        ),
                      if (visibleRows.isEmpty)
                        const EmptyStateCard(
                          icon: Icons.event_busy_outlined,
                          title: 'No Bookings Found',
                          message:
                              'Try another status filter or create a new booking.',
                        )
                      else
                        ...visibleRows.map((item) {
                          final bookingId = (item['id'] as num?)?.toInt() ?? 0;
                          final pending = _pendingIds.contains(bookingId);
                          final status = item['status']?.toString() ?? '';
                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(14),
                              gradient: const LinearGradient(
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                                colors: [
                                  Color(0xF7FFFFFF),
                                  Color(0xEFFFFFFF),
                                ],
                              ),
                              border:
                                  Border.all(color: const Color(0xFFD8E2F0)),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Expanded(
                                      child: Text(
                                        item['reference']
                                                    ?.toString()
                                                    .isNotEmpty ==
                                                true
                                            ? item['reference'].toString()
                                            : 'Booking #${item['id']}',
                                        style: const TextStyle(
                                          fontWeight: FontWeight.w700,
                                          fontSize: 15,
                                        ),
                                      ),
                                    ),
                                    _statusChip(status),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  '${item['customer_name'] ?? ''} - ${item['vehicle_display'] ?? ''}',
                                  style: const TextStyle(
                                    color: Color(0xFF4A5876),
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                const SizedBox(height: 3),
                                Text(
                                  '${item['pickup_date'] ?? ''} -> ${item['return_date'] ?? ''}',
                                  style: const TextStyle(
                                    color: Color(0xFF7583A0),
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                                const SizedBox(height: 6),
                                if (pending)
                                  const Chip(
                                    label: Text('Pending Sync'),
                                    visualDensity: VisualDensity.compact,
                                  ),
                                TextButton(
                                  onPressed: () {
                                    if (bookingId <= 0) return;
                                    Navigator.pushNamed(
                                      context,
                                      AppRoutes.bookingDetail,
                                      arguments: bookingId,
                                    ).then((_) => _load());
                                  },
                                  child: const Text('Open Details'),
                                ),
                                const SizedBox(height: 4),
                                _buildActions(item),
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
