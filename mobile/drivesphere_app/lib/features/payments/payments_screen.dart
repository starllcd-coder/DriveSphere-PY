import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

import '../../core/utils/app_message_helper.dart';
import '../../core/utils/app_validators.dart';
import '../../models/payment_model.dart';
import '../../services/api_service.dart';
import '../../widgets/app_empty_state.dart';
import '../../widgets/app_error_state.dart';
import '../../widgets/app_loading_indicator.dart';
import '../../widgets/app_primary_button.dart';
import '../../widgets/app_snackbar.dart';

class PaymentsScreen extends StatefulWidget {
  const PaymentsScreen({super.key});

  @override
  State<PaymentsScreen> createState() => _PaymentsScreenState();
}

class _PaymentsScreenState extends State<PaymentsScreen> {
  final ApiService _apiService = ApiService();

  final TextEditingController _bookingIdController = TextEditingController();
  final TextEditingController _amountController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();

  String _selectedMethod = 'CARD';
  bool _creating = false;

  late Future<List<PaymentModel>> _paymentsFuture;

  final List<String> _methods = [
    'CARD',
    'APPLE_PAY',
    'GOOGLE_PAY',
    'CASH_ON_PICKUP',
  ];

  @override
  void initState() {
    super.initState();
    _paymentsFuture = _apiService.fetchPayments();
  }

  Future<void> _refreshPayments() async {
    setState(() {
      _paymentsFuture = _apiService.fetchPayments();
    });
  }

  Future<void> _createPayment() async {
    final bookingError = AppValidators.integerId(
        _bookingIdController.text, 'payments.booking_id'.tr());
    final amountError = AppValidators.positiveNumber(
        _amountController.text, 'payments.amount'.tr());

    if (bookingError != null) {
      AppSnackBar.error(context, bookingError);
      return;
    }

    if (amountError != null) {
      AppSnackBar.error(context, amountError);
      return;
    }

    setState(() {
      _creating = true;
    });

    try {
      await _apiService.createPayment(
        bookingId: int.parse(_bookingIdController.text.trim()),
        amount: _amountController.text.trim(),
        method: _selectedMethod,
        notes: _notesController.text.trim(),
      );

      _bookingIdController.clear();
      _amountController.clear();
      _notesController.clear();

      setState(() {
        _paymentsFuture = _apiService.fetchPayments();
      });

      if (!mounted) return;
      AppSnackBar.success(context, 'payments.created_success'.tr());
    } catch (e) {
      if (!mounted) return;
      AppSnackBar.error(context, AppMessageHelper.extractErrorMessage(e));
    } finally {
      if (mounted) {
        setState(() {
          _creating = false;
        });
      }
    }
  }

  Color _statusColor(String status) {
    switch (status.toUpperCase()) {
      case 'COMPLETED':
      case 'PAID':
        return const Color(0xFF179D57);
      case 'PENDING':
        return const Color(0xFFD28A17);
      case 'FAILED':
        return const Color(0xFFD14848);
      default:
        return const Color(0xFF6B7280);
    }
  }

  @override
  void dispose() {
    _bookingIdController.dispose();
    _amountController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text(
          'payments.title'.tr(),
          style: const TextStyle(
            color: Color(0xFF1C3566),
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
      ),
      body: RefreshIndicator(
        onRefresh: _refreshPayments,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          children: [
            _createPaymentCard(),
            const SizedBox(height: 16),
            FutureBuilder<List<PaymentModel>>(
              future: _paymentsFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return Padding(
                    padding: const EdgeInsets.only(top: 40),
                    child:
                        AppLoadingIndicator(message: 'payments.loading'.tr()),
                  );
                }

                if (snapshot.hasError) {
                  return AppErrorState(
                    title: 'payments.failed_load'.tr(),
                    subtitle: 'payments.failed_load_subtitle'.tr(),
                    onRetry: _refreshPayments,
                  );
                }

                final payments = snapshot.data ?? [];

                if (payments.isEmpty) {
                  return AppEmptyState(
                    icon: Icons.credit_card_outlined,
                    title: 'payments.empty_title'.tr(),
                    subtitle: 'payments.empty_subtitle'.tr(),
                  );
                }

                return Column(
                  children: payments
                      .map(
                        (payment) => Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: _paymentCard(payment),
                        ),
                      )
                      .toList(),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _createPaymentCard() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFFFFF), Color(0xFFF6FAFF)],
        ),
        border: Border.all(color: const Color(0xFFDCE5F3)),
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF9DA8BE).withAlpha(28),
            blurRadius: 16,
            offset: const Offset(0, 9),
          ),
        ],
      ),
      child: Column(
        children: [
          _textField(
            controller: _bookingIdController,
            label: 'payments.booking_id'.tr(),
            hint: '1',
            keyboardType: TextInputType.number,
          ),
          const SizedBox(height: 14),
          _textField(
            controller: _amountController,
            label: 'payments.amount'.tr(),
            hint: '25.000',
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
          ),
          const SizedBox(height: 14),
          DropdownButtonFormField<String>(
            initialValue: _selectedMethod,
            decoration: InputDecoration(
              labelText: 'payments.method'.tr(),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
              ),
            ),
            items: _methods
                .map(
                  (item) => DropdownMenuItem(
                    value: item,
                    child: Text(item),
                  ),
                )
                .toList(),
            onChanged: (value) {
              if (value != null) {
                setState(() {
                  _selectedMethod = value;
                });
              }
            },
          ),
          const SizedBox(height: 14),
          _textField(
            controller: _notesController,
            label: 'payments.notes'.tr(),
            hint: 'common.optional'.tr(),
            maxLines: 3,
          ),
          const SizedBox(height: 16),
          AppPrimaryButton(
            label: 'payments.create_payment'.tr(),
            loading: _creating,
            onPressed: _createPayment,
          ),
        ],
      ),
    );
  }

  Widget _paymentCard(PaymentModel payment) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFFFFF), Color(0xFFF6FAFF)],
        ),
        border: Border.all(color: const Color(0xFFDCE5F3)),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF9DA8BE).withAlpha(28),
            blurRadius: 14,
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
                  payment.vehicleDisplay.isNotEmpty
                      ? payment.vehicleDisplay
                      : 'Payment #${payment.id}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF162E60),
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 5,
                ),
                decoration: BoxDecoration(
                  color: _statusColor(payment.status).withAlpha(31),
                  borderRadius: BorderRadius.circular(24),
                ),
                child: Text(
                  payment.status,
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: _statusColor(payment.status),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          _row('payments.receipt'.tr(),
              payment.receiptNumber.isNotEmpty ? payment.receiptNumber : '-'),
          _row(
              'payments.booking_ref'.tr(),
              payment.bookingReference.isNotEmpty
                  ? payment.bookingReference
                  : '-'),
          _row('payments.method'.tr(), payment.method),
          _row('payments.date'.tr(),
              payment.paymentDate.isNotEmpty ? payment.paymentDate : '-'),
          const SizedBox(height: 10),
          Row(
            children: [
              Text(
                'payments.amount_label'.tr(),
                style: const TextStyle(
                  fontSize: 13,
                  color: Color(0xFF6B7280),
                ),
              ),
              const Spacer(),
              Text(
                '${payment.currencyCode} ${payment.amount.toStringAsFixed(3)}',
                style: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF1C3566),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(
            width: 90,
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 12.5,
                color: Color(0xFF7B8192),
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 12.5,
                fontWeight: FontWeight.w600,
                color: Color(0xFF162E60),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _textField({
    required TextEditingController controller,
    required String label,
    required String hint,
    TextInputType keyboardType = TextInputType.text,
    int maxLines = 1,
  }) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      maxLines: maxLines,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
        ),
      ),
    );
  }
}
