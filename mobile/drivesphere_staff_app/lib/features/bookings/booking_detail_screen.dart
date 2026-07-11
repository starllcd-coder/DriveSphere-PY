import 'package:flutter/material.dart';

import '../../services/staff_api_service.dart';
import '../../widgets/staff_scaffold.dart';

class BookingDetailScreen extends StatefulWidget {
  final int bookingId;

  const BookingDetailScreen({super.key, required this.bookingId});

  @override
  State<BookingDetailScreen> createState() => _BookingDetailScreenState();
}

class _BookingDetailScreenState extends State<BookingDetailScreen> {
  final _api = StaffApiService();
  bool _loading = true;
  String _error = '';
  Map<String, dynamic> _item = const {};

  final _pickupDateController = TextEditingController();
  final _returnDateController = TextEditingController();
  final _pickupLocationController = TextEditingController();
  final _returnLocationController = TextEditingController();
  final _notesController = TextEditingController();
  String _status = 'CONFIRMED';

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
      final detail = await _api.fetchBookingDetail(widget.bookingId);
      if (!mounted) return;
      setState(() {
        _item = detail;
        _pickupDateController.text = detail['pickup_date']?.toString() ?? '';
        _returnDateController.text = detail['return_date']?.toString() ?? '';
        _pickupLocationController.text = detail['pickup_location']?.toString() ?? '';
        _returnLocationController.text = detail['return_location']?.toString() ?? '';
        _notesController.text = detail['notes']?.toString() ?? '';
        _status = detail['status']?.toString() ?? 'CONFIRMED';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    try {
      final result = await _api.updateBooking(
        bookingId: widget.bookingId,
        payload: {
          'pickup_date': _pickupDateController.text.trim(),
          'return_date': _returnDateController.text.trim(),
          'pickup_location': _pickupLocationController.text.trim(),
          'return_location': _returnLocationController.text.trim(),
          'notes': _notesController.text.trim(),
          'status': _status,
        },
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            result['queued'] == true
                ? 'No network. Update queued and will sync automatically.'
                : 'Booking updated successfully',
          ),
        ),
      );
      await _load();
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
      title: 'Booking #${widget.bookingId}',
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error.isNotEmpty
              ? Center(child: Text(_error))
              : ListView(
                  children: [
                    Text(
                      _item['reference']?.toString().isNotEmpty == true
                          ? _item['reference'].toString()
                          : 'Reference unavailable',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Text('Customer: ${_item['customer_name'] ?? ''}'),
                    Text('Vehicle: ${_item['vehicle_display'] ?? ''}'),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _pickupDateController,
                      decoration: const InputDecoration(labelText: 'Pickup Date (YYYY-MM-DD)'),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _returnDateController,
                      decoration: const InputDecoration(labelText: 'Return Date (YYYY-MM-DD)'),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _pickupLocationController,
                      decoration: const InputDecoration(labelText: 'Pickup Location'),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _returnLocationController,
                      decoration: const InputDecoration(labelText: 'Return Location'),
                    ),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<String>(
                      initialValue: _status,
                      decoration: const InputDecoration(labelText: 'Status'),
                      items: const [
                        DropdownMenuItem(value: 'DRAFT', child: Text('Draft')),
                        DropdownMenuItem(value: 'CONFIRMED', child: Text('Confirmed')),
                        DropdownMenuItem(value: 'UPCOMING', child: Text('Upcoming')),
                        DropdownMenuItem(value: 'CHECKED_OUT', child: Text('Checked Out')),
                        DropdownMenuItem(value: 'RETURNED', child: Text('Returned')),
                        DropdownMenuItem(value: 'CLOSED', child: Text('Closed')),
                        DropdownMenuItem(value: 'CANCELLED', child: Text('Cancelled')),
                      ],
                      onChanged: (value) {
                        if (value == null) return;
                        setState(() => _status = value);
                      },
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _notesController,
                      minLines: 2,
                      maxLines: 4,
                      decoration: const InputDecoration(labelText: 'Notes'),
                    ),
                    const SizedBox(height: 12),
                    FilledButton(
                      onPressed: _save,
                      child: const Text('Save Changes'),
                    ),
                  ],
                ),
    );
  }
}
