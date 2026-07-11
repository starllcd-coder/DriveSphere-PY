import 'dart:async';
import 'dart:convert';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';

import '../../services/staff_api_service.dart';
import '../../widgets/brand_button.dart';
import '../../widgets/staff_scaffold.dart';

class BookingWizardScreen extends StatefulWidget {
  const BookingWizardScreen({super.key});

  @override
  State<BookingWizardScreen> createState() => _BookingWizardScreenState();
}

class _BookingWizardScreenState extends State<BookingWizardScreen> {
  final _api = StaffApiService();

  final _customerSearchController = TextEditingController();
  final _customerNameController = TextEditingController();
  final _customerIdTypeController = TextEditingController(text: 'ID');
  final _customerIdNumberController = TextEditingController();
  final _customerPhoneController = TextEditingController();
  final _customerEmailController = TextEditingController();
  final _customerAddressController = TextEditingController();
  final _customerLicenseNumberController = TextEditingController();
  final _customerLicenseIssuerController = TextEditingController();
  final _customerLicenseIssueDateController = TextEditingController();
  final _customerLicenseExpiryDateController = TextEditingController();

  final _pickupDateController = TextEditingController();
  final _returnDateController = TextEditingController();
  final _pickupTimeController = TextEditingController();
  final _returnTimeController = TextEditingController();
  final _pickupLocationController = TextEditingController();
  final _returnLocationController = TextEditingController();

  final _vatRateController = TextEditingController(text: '0.050');
  final _depositController = TextEditingController();
  final _notesController = TextEditingController();

  final _odometerController = TextEditingController();
  final _fuelController = TextEditingController(text: '100');

  final _signatureKey = GlobalKey();
  final List<Offset?> _signaturePoints = [];

  Timer? _searchDebounce;
  int _stepIndex = 0;
  bool _isExistingCustomer = true;
  bool _loadingCustomers = false;
  bool _loadingVehicles = false;
  bool _submitting = false;
  String _error = '';

  int? _selectedCustomerId;
  List<Map<String, dynamic>> _customerResults = const [];
  List<Map<String, dynamic>> _availableVehicles = const [];
  int? _selectedVehicleId;
  double _selectedVehicleRate = 0;
  double _selectedVehicleDeposit = 0;

  bool _handoverSpare = false;
  bool _handoverJack = false;
  bool _handoverTriangle = false;
  bool _handoverDocs = false;
  bool _handoverChildSeat = false;
  bool _handoverGps = false;
  bool _checkoutNow = false;

  final List<_DriverEntry> _drivers = [
    _DriverEntry(),
  ];

  late final List<_ExtraOption> _extras = [
    _ExtraOption(keyName: 'baby_seat', label: 'Baby Seat', rate: '2.000'),
    _ExtraOption(keyName: 'gps', label: 'GPS', rate: '1.000'),
    _ExtraOption(keyName: 'driver_service', label: 'Driver Service', rate: '10.000'),
    _ExtraOption(keyName: 'fuel_package', label: 'Fuel Package', rate: '5.000'),
    _ExtraOption(keyName: 'wifi_router', label: 'WiFi Router', rate: '3.000'),
  ];

  final List<String> _stepLabels = const [
    'Customer',
    'Driver',
    'Dates',
    'Vehicle',
    'Extras',
    'Pricing',
    'Signature',
    'Handover',
    'Finish',
  ];

  @override
  void dispose() {
    _searchDebounce?.cancel();
    _customerSearchController.dispose();
    _customerNameController.dispose();
    _customerIdTypeController.dispose();
    _customerIdNumberController.dispose();
    _customerPhoneController.dispose();
    _customerEmailController.dispose();
    _customerAddressController.dispose();
    _customerLicenseNumberController.dispose();
    _customerLicenseIssuerController.dispose();
    _customerLicenseIssueDateController.dispose();
    _customerLicenseExpiryDateController.dispose();
    _pickupDateController.dispose();
    _returnDateController.dispose();
    _pickupTimeController.dispose();
    _returnTimeController.dispose();
    _pickupLocationController.dispose();
    _returnLocationController.dispose();
    _vatRateController.dispose();
    _depositController.dispose();
    _notesController.dispose();
    _odometerController.dispose();
    _fuelController.dispose();
    for (final driver in _drivers) {
      driver.dispose();
    }
    for (final extra in _extras) {
      extra.dispose();
    }
    super.dispose();
  }
  Future<void> _searchCustomers() async {
    final query = _customerSearchController.text.trim();
    if (query.isEmpty) {
      setState(() => _customerResults = const []);
      return;
    }
    setState(() => _loadingCustomers = true);
    try {
      final results = await _api.fetchCustomers(query: query);
      if (!mounted) return;
      setState(() => _customerResults = results);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _loadingCustomers = false);
    }
  }

  void _onCustomerSearchChanged() {
    _searchDebounce?.cancel();
    _searchDebounce = Timer(const Duration(milliseconds: 350), _searchCustomers);
  }

  void _selectCustomer(Map<String, dynamic> customer) {
    setState(() {
      _selectedCustomerId = (customer['id'] as num?)?.toInt();
      _customerNameController.text = customer['name']?.toString() ?? '';
      _customerIdTypeController.text = customer['id_type']?.toString() ?? 'ID';
      _customerIdNumberController.text = customer['id_number']?.toString() ?? '';
      _customerPhoneController.text = customer['phone_number']?.toString() ?? '';
      _customerEmailController.text = customer['email']?.toString() ?? '';
      _customerAddressController.text = customer['address']?.toString() ?? '';
      _customerLicenseNumberController.text = customer['license_number']?.toString() ?? '';
      _customerLicenseIssuerController.text = customer['license_issuer']?.toString() ?? '';
      _customerLicenseIssueDateController.text = customer['license_issue_date']?.toString() ?? '';
      _customerLicenseExpiryDateController.text = customer['license_expiry_date']?.toString() ?? '';
      _isExistingCustomer = true;
    });
  }

  Future<void> _pickDate(TextEditingController controller) async {
    final now = DateTime.now();
    final current = DateTime.tryParse(controller.text.trim());
    final selected = await showDatePicker(
      context: context,
      initialDate: current ?? now,
      firstDate: DateTime(now.year - 1),
      lastDate: DateTime(now.year + 5),
    );
    if (selected == null) return;
    controller.text = selected.toIso8601String().split('T').first;
    await _loadAvailableVehicles();
    setState(() {});
  }

  Future<void> _pickTime(TextEditingController controller) async {
    final initial = TimeOfDay.now();
    final selected = await showTimePicker(context: context, initialTime: initial);
    if (selected == null) return;
    final hour = selected.hour.toString().padLeft(2, '0');
    final minute = selected.minute.toString().padLeft(2, '0');
    controller.text = '$hour:$minute:00';
    setState(() {});
  }

  Future<void> _loadAvailableVehicles() async {
    final pickup = _pickupDateController.text.trim();
    final ret = _returnDateController.text.trim();
    if (pickup.isEmpty || ret.isEmpty) return;

    setState(() => _loadingVehicles = true);
    try {
      final results = await _api.fetchAvailableVehicles(
        pickupDate: pickup,
        returnDate: ret,
      );
      if (!mounted) return;
      setState(() {
        _availableVehicles = results;
        if (_selectedVehicleId != null) {
          final exists = results.any(
            (item) => (item['id'] as num?)?.toInt() == _selectedVehicleId,
          );
          if (!exists) {
            _selectedVehicleId = null;
            _selectedVehicleRate = 0;
            _selectedVehicleDeposit = 0;
          }
        }
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _loadingVehicles = false);
    }
  }

  void _selectVehicle(int? vehicleId) {
    if (vehicleId == null) return;
    final match = _availableVehicles.firstWhere(
      (item) => (item['id'] as num?)?.toInt() == vehicleId,
      orElse: () => const {},
    );
    setState(() {
      _selectedVehicleId = vehicleId;
      _selectedVehicleRate = (match['rate'] as num?)?.toDouble() ?? 0;
      _selectedVehicleDeposit = (match['deposit'] as num?)?.toDouble() ?? 0;
      if (_depositController.text.trim().isEmpty) {
        _depositController.text = _selectedVehicleDeposit.toStringAsFixed(3);
      }
    });
  }

  double _extrasTotal() {
    var total = 0.0;
    for (final extra in _extras) {
      if (!extra.selected) continue;
      final qty = int.tryParse(extra.qtyController.text.trim()) ?? 1;
      final rate = double.tryParse(extra.rateController.text.trim()) ?? 0;
      total += qty * rate;
    }
    return total;
  }

  int _rentalDays() {
    final pickup = DateTime.tryParse(_pickupDateController.text.trim());
    final ret = DateTime.tryParse(_returnDateController.text.trim());
    if (pickup == null || ret == null) return 0;
    final diff = ret.difference(pickup).inDays;
    return diff <= 0 ? 1 : diff;
  }

  bool _validateStep(int step) {
    setState(() => _error = '');
    if (step == 0) {
      if (_isExistingCustomer) {
        if (_selectedCustomerId == null) {
          setState(() => _error = 'Select an existing customer.');
          return false;
        }
      } else {
        if (_customerNameController.text.trim().isEmpty) {
          setState(() => _error = 'Customer name is required.');
          return false;
        }
      }
    }
    if (step == 2) {
      if (_pickupDateController.text.trim().isEmpty ||
          _returnDateController.text.trim().isEmpty) {
        setState(() => _error = 'Pickup and return dates are required.');
        return false;
      }
      final pickup = DateTime.tryParse(_pickupDateController.text.trim());
      final ret = DateTime.tryParse(_returnDateController.text.trim());
      if (pickup != null && ret != null && ret.isBefore(pickup)) {
        setState(() => _error = 'Return date cannot be before pickup date.');
        return false;
      }
    }
    if (step == 3) {
      if (_selectedVehicleId == null) {
        setState(() => _error = 'Select a vehicle from availability.');
        return false;
      }
    }
    return true;
  }

  void _goNext() {
    if (!_validateStep(_stepIndex)) return;
    if (_stepIndex < _stepLabels.length - 1) {
      setState(() => _stepIndex += 1);
    }
  }

  void _goBack() {
    if (_stepIndex > 0) {
      setState(() => _stepIndex -= 1);
    }
  }

  Future<String> _captureSignatureBase64() async {
    if (_signaturePoints.isEmpty) return '';
    final boundary =
        _signatureKey.currentContext?.findRenderObject() as RenderRepaintBoundary?;
    if (boundary == null) return '';
    final image = await boundary.toImage(pixelRatio: 2.0);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    if (bytes == null) return '';
    return base64Encode(bytes.buffer.asUint8List());
  }

  Future<void> _submitBooking() async {
    if (!_validateStep(3)) return;
    setState(() {
      _submitting = true;
      _error = '';
    });
    try {
      final signature = await _captureSignatureBase64();
      final extras = _extras
          .where((e) => e.selected)
          .map(
            (e) => {
              'key': e.keyName,
              'name': e.label,
              'qty': int.tryParse(e.qtyController.text.trim()) ?? 1,
              'unit_price': e.rateController.text.trim(),
            },
          )
          .toList();
      final drivers = _drivers
          .where((d) => d.nameController.text.trim().isNotEmpty)
          .map(
            (d) => {
              'name': d.nameController.text.trim(),
              'phone_number': d.phoneController.text.trim(),
              'id_number': d.idController.text.trim(),
              'license_number': d.licenseController.text.trim(),
            },
          )
          .toList();

      final result = await _api.createBooking(
        vehicleId: _selectedVehicleId ?? 0,
        pickupDate: _pickupDateController.text.trim(),
        returnDate: _returnDateController.text.trim(),
        customerId: _isExistingCustomer ? _selectedCustomerId : null,
        customerName: _customerNameController.text.trim(),
        customerPhoneNumber: _customerPhoneController.text.trim(),
        customerIdType: _customerIdTypeController.text.trim(),
        customerIdNumber: _customerIdNumberController.text.trim(),
        customerEmail: _customerEmailController.text.trim(),
        customerAddress: _customerAddressController.text.trim(),
        customerLicenseNumber: _customerLicenseNumberController.text.trim(),
        customerLicenseIssuer: _customerLicenseIssuerController.text.trim(),
        customerLicenseIssueDate:
            _customerLicenseIssueDateController.text.trim(),
        customerLicenseExpiryDate:
            _customerLicenseExpiryDateController.text.trim(),
        pickupTime: _pickupTimeController.text.trim(),
        returnTime: _returnTimeController.text.trim(),
        pickupLocation: _pickupLocationController.text.trim(),
        returnLocation: _returnLocationController.text.trim(),
        dailyRate: _selectedVehicleRate.toStringAsFixed(3),
        depositAmount: _depositController.text.trim(),
        vatRate: _vatRateController.text.trim(),
        extrasTotal: _extrasTotal().toStringAsFixed(3),
        extras: extras,
        drivers: drivers,
        notes: _notesController.text.trim(),
      );

      final queued = result['queued'] == true;

      if (_checkoutNow && !queued) {
        final bookingId = result['booking_id'] as int?;
        if (bookingId != null && bookingId > 0) {
          await _api.checkoutBooking(
            bookingId: bookingId,
            odometerOutKm: int.tryParse(_odometerController.text.trim()) ?? 0,
            fuelOutPercent: int.tryParse(_fuelController.text.trim()) ?? 100,
            checklist: {
              'spare': _handoverSpare,
              'jack': _handoverJack,
              'triangle': _handoverTriangle,
              'docs': _handoverDocs,
              'child_seat': _handoverChildSeat,
              'gps': _handoverGps,
            },
            signature: signature,
          );
        }
      }

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            queued
                ? 'No network. Booking queued for sync.'
                : 'Booking created successfully.',
          ),
        ),
      );
      Navigator.pop(context);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }
  Widget _buildStepIndicator() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: List.generate(_stepLabels.length, (index) {
          final active = index == _stepIndex;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: Text('${index + 1}. ${_stepLabels[index]}'),
              selected: active,
              onSelected: (_) => setState(() => _stepIndex = index),
            ),
          );
        }),
      ),
    );
  }

  Widget _buildCustomerStep() {
    final readOnly = _isExistingCustomer;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Customer Details', style: TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          children: [
            ChoiceChip(
              label: const Text('Existing'),
              selected: _isExistingCustomer,
              onSelected: (_) => setState(() => _isExistingCustomer = true),
            ),
            ChoiceChip(
              label: const Text('New'),
              selected: !_isExistingCustomer,
              onSelected: (_) => setState(() => _isExistingCustomer = false),
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (_isExistingCustomer) ...[
          TextField(
            controller: _customerSearchController,
            onChanged: (_) => _onCustomerSearchChanged(),
            decoration: const InputDecoration(
              labelText: 'Search by name, phone, or ID',
              prefixIcon: Icon(Icons.search),
            ),
          ),
          const SizedBox(height: 8),
          if (_loadingCustomers) const LinearProgressIndicator(),
          if (_customerResults.isNotEmpty)
            SizedBox(
              height: 180,
              child: ListView.separated(
                itemCount: _customerResults.length,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (context, index) {
                  final customer = _customerResults[index];
                  final id = (customer['id'] as num?)?.toInt();
                  return ListTile(
                    title: Text(customer['name']?.toString() ?? 'Unknown'),
                    subtitle: Text('${customer['phone_number'] ?? '-'} | ${customer['id_number'] ?? '-'}'),
                    trailing: Icon(
                      (_selectedCustomerId != null && id == _selectedCustomerId)
                          ? Icons.check_circle
                          : Icons.radio_button_unchecked,
                      color: (_selectedCustomerId != null && id == _selectedCustomerId)
                          ? const Color(0xFF1F4E8C)
                          : const Color(0xFF96A3B8),
                    ),
                    onTap: () => _selectCustomer(customer),
                  );
                },
              ),
            ),
          const SizedBox(height: 8),
        ],
        _buildCustomerForm(readOnly: readOnly),
      ],
    );
  }

  Widget _buildCustomerForm({required bool readOnly}) {
    return Column(
      children: [
        TextField(
          controller: _customerNameController,
          readOnly: readOnly,
          decoration: const InputDecoration(labelText: 'Customer Name'),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _customerIdTypeController,
          readOnly: readOnly,
          decoration: const InputDecoration(labelText: 'ID Type'),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _customerIdNumberController,
          readOnly: readOnly,
          decoration: const InputDecoration(labelText: 'ID Number'),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _customerPhoneController,
          readOnly: readOnly,
          decoration: const InputDecoration(labelText: 'Phone Number'),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _customerEmailController,
          readOnly: readOnly,
          decoration: const InputDecoration(labelText: 'Email'),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _customerAddressController,
          readOnly: readOnly,
          decoration: const InputDecoration(labelText: 'Address'),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _customerLicenseNumberController,
          readOnly: readOnly,
          decoration: const InputDecoration(labelText: 'License Number'),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _customerLicenseIssuerController,
          readOnly: readOnly,
          decoration: const InputDecoration(labelText: 'License Issuer'),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _customerLicenseIssueDateController,
                readOnly: readOnly,
                decoration: const InputDecoration(labelText: 'License Issue Date'),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: _customerLicenseExpiryDateController,
                readOnly: readOnly,
                decoration: const InputDecoration(labelText: 'License Expiry Date'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildDriverStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Additional Drivers', style: TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        ..._drivers.asMap().entries.map((entry) {
          final index = entry.key;
          final driver = entry.value;
          return Card(
            margin: const EdgeInsets.only(bottom: 10),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                children: [
                  Row(
                    children: [
                      Expanded(child: Text('Driver ${index + 1}')),
                      if (_drivers.length > 1)
                        IconButton(
                          onPressed: () {
                            setState(() {
                              _drivers.removeAt(index).dispose();
                            });
                          },
                          icon: const Icon(Icons.delete_outline),
                        ),
                    ],
                  ),
                  TextField(
                    controller: driver.nameController,
                    decoration: const InputDecoration(labelText: 'Name'),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: driver.phoneController,
                    decoration: const InputDecoration(labelText: 'Phone'),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: driver.idController,
                    decoration: const InputDecoration(labelText: 'ID Number'),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: driver.licenseController,
                    decoration: const InputDecoration(labelText: 'License Number'),
                  ),
                ],
              ),
            ),
          );
        }),
        Align(
          alignment: Alignment.centerLeft,
          child: OutlinedButton.icon(
            onPressed: () => setState(() => _drivers.add(_DriverEntry())),
            icon: const Icon(Icons.add),
            label: const Text('Add Driver'),
          ),
        ),
      ],
    );
  }
  Widget _buildDatesStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Rental Dates', style: TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _pickupDateController,
                readOnly: true,
                onTap: () => _pickDate(_pickupDateController),
                decoration: const InputDecoration(
                  labelText: 'Pickup Date',
                  suffixIcon: Icon(Icons.calendar_today),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: _returnDateController,
                readOnly: true,
                onTap: () => _pickDate(_returnDateController),
                decoration: const InputDecoration(
                  labelText: 'Return Date',
                  suffixIcon: Icon(Icons.calendar_today),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _pickupTimeController,
                readOnly: true,
                onTap: () => _pickTime(_pickupTimeController),
                decoration: const InputDecoration(
                  labelText: 'Pickup Time',
                  suffixIcon: Icon(Icons.schedule),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: _returnTimeController,
                readOnly: true,
                onTap: () => _pickTime(_returnTimeController),
                decoration: const InputDecoration(
                  labelText: 'Return Time',
                  suffixIcon: Icon(Icons.schedule),
                ),
              ),
            ),
          ],
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
      ],
    );
  }

  Widget _buildVehicleStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Select Vehicle', style: TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        if (_loadingVehicles) const LinearProgressIndicator(),
        DropdownButtonFormField<int>(
          initialValue: _selectedVehicleId,
          decoration: const InputDecoration(labelText: 'Available Vehicles'),
          items: _availableVehicles
              .map(
                (vehicle) => DropdownMenuItem<int>(
                  value: (vehicle['id'] as num?)?.toInt() ?? 0,
                  child: Text(
                    '${vehicle['name'] ?? ''} (${vehicle['plate'] ?? ''}) - ${vehicle['rate'] ?? ''}',
                  ),
                ),
              )
              .toList(),
          onChanged: _selectVehicle,
        ),
        const SizedBox(height: 12),
        Text('Daily Rate: ${_selectedVehicleRate.toStringAsFixed(3)}'),
        Text('Deposit: ${_selectedVehicleDeposit.toStringAsFixed(3)}'),
      ],
    );
  }

  Widget _buildExtrasStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Extras', style: TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        ..._extras.map(
          (extra) => Card(
            margin: const EdgeInsets.only(bottom: 8),
            child: Padding(
              padding: const EdgeInsets.all(10),
              child: Column(
                children: [
                  CheckboxListTile(
                    value: extra.selected,
                    onChanged: (value) => setState(() => extra.selected = value ?? false),
                    title: Text(extra.label),
                    controlAffinity: ListTileControlAffinity.leading,
                  ),
                  if (extra.selected)
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: extra.qtyController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(labelText: 'Qty'),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: TextField(
                            controller: extra.rateController,
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            decoration: const InputDecoration(labelText: 'Rate'),
                          ),
                        ),
                      ],
                    ),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),
        Text('Extras Total: ${_extrasTotal().toStringAsFixed(3)}'),
      ],
    );
  }

  Widget _buildPricingStep() {
    final days = _rentalDays();
    final subtotal = (days * _selectedVehicleRate) + _extrasTotal();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Pricing Summary', style: TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        Text('Days: $days'),
        Text('Daily Rate: ${_selectedVehicleRate.toStringAsFixed(3)}'),
        Text('Extras Total: ${_extrasTotal().toStringAsFixed(3)}'),
        Text('Subtotal: ${subtotal.toStringAsFixed(3)}'),
        const SizedBox(height: 12),
        TextField(
          controller: _vatRateController,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(labelText: 'VAT Rate (e.g. 0.050)'),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _depositController,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(labelText: 'Deposit Amount'),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _notesController,
          decoration: const InputDecoration(labelText: 'Notes'),
          maxLines: 2,
        ),
      ],
    );
  }
  Widget _buildSignatureStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Customer Signature', style: TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            border: Border.all(color: const Color(0xFFCBD4E1)),
            borderRadius: BorderRadius.circular(12),
          ),
          child: RepaintBoundary(
            key: _signatureKey,
            child: GestureDetector(
              onPanUpdate: (details) {
                setState(() {
                  final box =
                      _signatureKey.currentContext?.findRenderObject() as RenderBox?;
                  final local = box?.globalToLocal(details.globalPosition);
                  if (local != null) {
                    _signaturePoints.add(local);
                  }
                });
              },
              onPanEnd: (_) => _signaturePoints.add(null),
              child: CustomPaint(
                painter: _SignaturePainter(_signaturePoints),
                child: const SizedBox(height: 180, width: double.infinity),
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: () => setState(() => _signaturePoints.clear()),
          icon: const Icon(Icons.delete_outline),
          label: const Text('Clear Signature'),
        ),
      ],
    );
  }

  Widget _buildHandoverStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Handover Checklist', style: TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        TextField(
          controller: _odometerController,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'Odometer Out (km)'),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _fuelController,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'Fuel Out (%)'),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          children: [
            FilterChip(
              label: const Text('Spare'),
              selected: _handoverSpare,
              onSelected: (value) => setState(() => _handoverSpare = value),
            ),
            FilterChip(
              label: const Text('Jack'),
              selected: _handoverJack,
              onSelected: (value) => setState(() => _handoverJack = value),
            ),
            FilterChip(
              label: const Text('Triangle'),
              selected: _handoverTriangle,
              onSelected: (value) => setState(() => _handoverTriangle = value),
            ),
            FilterChip(
              label: const Text('Docs'),
              selected: _handoverDocs,
              onSelected: (value) => setState(() => _handoverDocs = value),
            ),
            FilterChip(
              label: const Text('Child Seat'),
              selected: _handoverChildSeat,
              onSelected: (value) => setState(() => _handoverChildSeat = value),
            ),
            FilterChip(
              label: const Text('GPS'),
              selected: _handoverGps,
              onSelected: (value) => setState(() => _handoverGps = value),
            ),
          ],
        ),
        const SizedBox(height: 8),
        SwitchListTile(
          value: _checkoutNow,
          onChanged: (value) => setState(() => _checkoutNow = value),
          title: const Text('Checkout now if pickup date is today'),
        ),
      ],
    );
  }

  Widget _buildFinishStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Review & Create', style: TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        Text('Customer: ${_customerNameController.text.trim()}'),
        Text('Dates: ${_pickupDateController.text.trim()} -> ${_returnDateController.text.trim()}'),
        Text('Vehicle: ${_selectedVehicleId ?? ''}'),
        Text('Extras Total: ${_extrasTotal().toStringAsFixed(3)}'),
        const SizedBox(height: 12),
        BrandButton(
          label: _submitting ? 'Creating...' : 'Create Booking',
          loading: _submitting,
          onPressed: _submitting ? null : _submitBooking,
        ),
      ],
    );
  }

  Widget _buildStepContent() {
    switch (_stepIndex) {
      case 0:
        return _buildCustomerStep();
      case 1:
        return _buildDriverStep();
      case 2:
        return _buildDatesStep();
      case 3:
        return _buildVehicleStep();
      case 4:
        return _buildExtrasStep();
      case 5:
        return _buildPricingStep();
      case 6:
        return _buildSignatureStep();
      case 7:
        return _buildHandoverStep();
      case 8:
      default:
        return _buildFinishStep();
    }
  }

  @override
  Widget build(BuildContext context) {
    return StaffScaffold(
      title: 'New Booking',
      body: Column(
        children: [
          _buildStepIndicator(),
          const SizedBox(height: 12),
          if (_error.isNotEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFFFCE8E6),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFFF7B6B0)),
              ),
              child: Text(_error, style: const TextStyle(color: Color(0xFFB93830))),
            ),
          const SizedBox(height: 8),
          Expanded(
            child: SingleChildScrollView(
              child: _buildStepContent(),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              if (_stepIndex > 0)
                Expanded(
                  child: OutlinedButton(
                    onPressed: _goBack,
                    child: const Text('Back'),
                  ),
                ),
              if (_stepIndex > 0) const SizedBox(width: 8),
              Expanded(
                child: BrandButton(
                  label: _stepIndex == _stepLabels.length - 1 ? 'Create Booking' : 'Next',
                  onPressed:
                      _stepIndex == _stepLabels.length - 1 ? _submitBooking : _goNext,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _DriverEntry {
  final nameController = TextEditingController();
  final phoneController = TextEditingController();
  final idController = TextEditingController();
  final licenseController = TextEditingController();

  void dispose() {
    nameController.dispose();
    phoneController.dispose();
    idController.dispose();
    licenseController.dispose();
  }
}

class _ExtraOption {
  final String keyName;
  final String label;
  bool selected = false;
  final TextEditingController qtyController;
  final TextEditingController rateController;

  _ExtraOption({
    required this.keyName,
    required this.label,
    String rate = '0.000',
  })  : qtyController = TextEditingController(text: '1'),
        rateController = TextEditingController(text: rate);

  void dispose() {
    qtyController.dispose();
    rateController.dispose();
  }
}

class _SignaturePainter extends CustomPainter {
  final List<Offset?> points;

  _SignaturePainter(this.points);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF1F4E8C)
      ..strokeCap = StrokeCap.round
      ..strokeWidth = 2.4;
    for (var i = 0; i < points.length - 1; i++) {
      final p1 = points[i];
      final p2 = points[i + 1];
      if (p1 != null && p2 != null) {
        canvas.drawLine(p1, p2, paint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _SignaturePainter oldDelegate) {
    return oldDelegate.points != points;
  }
}
