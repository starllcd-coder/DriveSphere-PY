import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/routes/app_routes.dart';
import '../../models/booking_model.dart';
import '../../services/api_service.dart';
import '../../widgets/app_empty_state.dart';
import '../../widgets/app_error_state.dart';
import '../../widgets/app_skeleton.dart';

class BookingHistoryScreen extends StatefulWidget {
  final bool embeddedInShell;

  const BookingHistoryScreen({
    super.key,
    this.embeddedInShell = false,
  });

  @override
  State<BookingHistoryScreen> createState() => _BookingHistoryScreenState();
}

class _BookingHistoryScreenState extends State<BookingHistoryScreen> {
  final ApiService _apiService = ApiService();
  late Future<List<BookingModel>> _bookingsFuture;
  String _segment = 'ALL';
  bool _retrying = false;

  @override
  void initState() {
    super.initState();
    _bookingsFuture = _apiService.fetchBookings();
  }

  Future<void> _refreshBookings() async {
    final next = _apiService.fetchBookings();
    setState(() {
      _retrying = true;
      _bookingsFuture = next;
    });
    try {
      await next;
    } catch (_) {}
    if (!mounted) return;
    setState(() => _retrying = false);
  }

  Future<void> _openWhatsApp(BookingModel booking) async {
    final text = Uri.encodeComponent(
      'Hello, I need help with booking ${booking.reference}.',
    );
    final url = Uri.parse('https://wa.me/96890000000?text=$text');
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    }
  }

  Color _statusColor(String status) {
    switch (status.toUpperCase()) {
      case 'BOOKING_REQUESTED':
        return const Color(0xFFD28A17);
      case 'CONFIRMED':
        return const Color(0xFF179D57);
      case 'VEHICLE_READY':
        return const Color(0xFF1F7AB8);
      case 'DRAFT':
        return const Color(0xFFD28A17);
      case 'ACTIVE':
        return const Color(0xFF234E8C);
      case 'COMPLETED':
        return const Color(0xFF5B6475);
      case 'CANCELLED':
        return const Color(0xFFD14848);
      default:
        return const Color(0xFF6B7280);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        automaticallyImplyLeading: !widget.embeddedInShell,
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text(
          'booking.history_title'.tr(),
          style: const TextStyle(
            color: Color(0xFF1C3566),
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
        actions: [
          IconButton(
            onPressed: () =>
                Navigator.pushNamed(context, AppRoutes.bookingCart),
            icon: const Icon(Icons.shopping_cart_outlined,
                color: Color(0xFF1C3566)),
          ),
          IconButton(
            onPressed: () => Navigator.pushNamed(context, AppRoutes.payments),
            icon:
                const Icon(Icons.credit_card_rounded, color: Color(0xFF1C3566)),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refreshBookings,
        child: FutureBuilder<List<BookingModel>>(
          future: _bookingsFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const AppSkeletonList(itemHeight: 210, count: 4);
            }

            if (snapshot.hasError) {
              return AppErrorState(
                title: 'booking.failed_load'.tr(),
                subtitle: 'booking.failed_load_subtitle'.tr(),
                onRetry: _refreshBookings,
                isRetrying: _retrying,
              );
            }

            final bookings = snapshot.data ?? [];
            final visibleBookings = bookings.where((booking) {
              if (_segment == 'ALL') return true;
              final status = booking.status.toUpperCase();
              if (_segment == 'UPCOMING') {
                return status == 'DRAFT' ||
                    status == 'BOOKING_REQUESTED' ||
                    status == 'CONFIRMED' ||
                    status == 'VEHICLE_READY';
              }
              if (_segment == 'ACTIVE') {
                return status == 'ACTIVE';
              }
              if (_segment == 'COMPLETED') {
                return status == 'COMPLETED';
              }
              if (_segment == 'CANCELLED') {
                return status == 'CANCELLED';
              }
              return true;
            }).toList();

            if (bookings.isEmpty) {
              return AppEmptyState(
                icon: Icons.receipt_long_outlined,
                title: 'booking.empty_title'.tr(),
                subtitle: 'booking.empty_subtitle'.tr(),
                buttonLabel: 'booking.browse_vehicles'.tr(),
                onPressed: () =>
                    Navigator.pushNamed(context, AppRoutes.vehicles),
              );
            }

            return Column(
              children: [
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 10),
                  child: Wrap(
                    spacing: 8,
                    children: [
                      _segmentChip('ALL', 'All'),
                      _segmentChip('UPCOMING', 'Upcoming'),
                      _segmentChip('ACTIVE', 'Active'),
                      _segmentChip('COMPLETED', 'Completed'),
                      _segmentChip('CANCELLED', 'Cancelled'),
                    ],
                  ),
                ),
                Expanded(
                  child: visibleBookings.isEmpty
                      ? AppEmptyState(
                          icon: Icons.filter_alt_off_outlined,
                          title: 'No bookings in this section',
                          subtitle: 'Try a different status filter.',
                        )
                      : ListView.separated(
                          padding: const EdgeInsets.fromLTRB(16, 6, 16, 24),
                          itemCount: visibleBookings.length,
                          separatorBuilder: (_, __) =>
                              const SizedBox(height: 14),
                          itemBuilder: (context, index) {
                            final booking = visibleBookings[index];

                            return Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                gradient: const LinearGradient(
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                  colors: [Color(0xFFFFFFFF), Color(0xFFF6FAFF)],
                                ),
                                border:
                                    Border.all(color: const Color(0xFFDCE5F3)),
                                borderRadius: BorderRadius.circular(22),
                                boxShadow: [
                                  BoxShadow(
                                    color:
                                        const Color(0xFF9DA8BE).withAlpha(28),
                                    blurRadius: 16,
                                    offset: const Offset(0, 9),
                                  ),
                                ],
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          booking.vehicleDisplay.isNotEmpty
                                              ? booking.vehicleDisplay
                                              : 'Booking #${booking.id}',
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                          style: const TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w700,
                                            color: Color(0xFF162E60),
                                          ),
                                        ),
                                      ),
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                            horizontal: 10, vertical: 5),
                                        decoration: BoxDecoration(
                                          color: _statusColor(booking.status)
                                              .withAlpha(31),
                                          borderRadius:
                                              BorderRadius.circular(24),
                                        ),
                                        child: Text(
                                          booking.status,
                                          style: TextStyle(
                                            fontSize: 11,
                                            fontWeight: FontWeight.w700,
                                            color: _statusColor(booking.status),
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 10),
                                  _row('Reference', booking.reference),
                                  _row('Company', booking.branchName),
                                  _row('Pickup', booking.pickupLocation),
                                  _row('Return', booking.returnLocation),
                                  _row(
                                    'Dates',
                                    '${booking.pickupDate} -> ${booking.returnDate}',
                                  ),
                                  _row(
                                    'Total',
                                    '${booking.currencyCode} ${booking.totalAmount.toStringAsFixed(2)}',
                                  ),
                                  const SizedBox(height: 8),
                                  _lifecycleTracker(booking.status),
                                  const SizedBox(height: 12),
                                  Row(
                                    children: [
                                      Expanded(
                                        child: OutlinedButton.icon(
                                          onPressed: () =>
                                              _openWhatsApp(booking),
                                          icon: const Icon(Icons.chat_outlined),
                                          label: const Text('WhatsApp'),
                                        ),
                                      ),
                                      const SizedBox(width: 10),
                                      Expanded(
                                        child: ElevatedButton.icon(
                                          onPressed: () => Navigator.pushNamed(
                                            context,
                                            AppRoutes.payments,
                                          ),
                                          icon: const Icon(
                                              Icons.credit_card_rounded),
                                          label: const Text('Payments'),
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _segmentChip(String value, String label) {
    final selected = _segment == value;
    return ChoiceChip(
      selected: selected,
      label: Text(label),
      onSelected: (_) => setState(() => _segment = value),
    );
  }

  Widget _lifecycleTracker(String status) {
    final stages = const [
      'BOOKING_REQUESTED',
      'CONFIRMED',
      'VEHICLE_READY',
      'ACTIVE',
      'COMPLETED',
    ];

    final normalized = status.toUpperCase();
    final activeIndex = stages.indexOf(normalized);

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: List.generate(stages.length, (index) {
        final stage = stages[index];
        final done = activeIndex >= index && activeIndex != -1;

        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: done
                ? const Color(0xFF234E8C).withAlpha(26)
                : const Color(0xFFF1F4F9),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: done ? const Color(0xFF234E8C) : const Color(0xFFE2E8F2),
            ),
          ),
          child: Text(
            _stageLabel(stage),
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: done ? const Color(0xFF234E8C) : const Color(0xFF7B8192),
            ),
          ),
        );
      }),
    );
  }

  String _stageLabel(String stage) {
    switch (stage) {
      case 'BOOKING_REQUESTED':
        return 'Requested';
      case 'CONFIRMED':
        return 'Confirmed';
      case 'VEHICLE_READY':
        return 'Ready';
      case 'ACTIVE':
        return 'Active';
      case 'COMPLETED':
        return 'Completed';
      default:
        return stage;
    }
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Expanded(
            child:
                Text(label, style: const TextStyle(color: Color(0xFF7B8192))),
          ),
          Expanded(
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                color: Color(0xFF162E60),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
