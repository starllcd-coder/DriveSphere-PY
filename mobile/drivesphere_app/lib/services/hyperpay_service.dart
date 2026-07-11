import 'package:flutter/services.dart';

import 'api_service.dart';

class HyperPayResult {
  final bool success;
  final String status;
  final String? transactionId;
  final String? message;

  const HyperPayResult({
    required this.success,
    required this.status,
    this.transactionId,
    this.message,
  });
}

class HyperPayService {
  static const MethodChannel _channel = MethodChannel('drivesphere/hyperpay');

  HyperPayService({required ApiService apiService}) : _apiService = apiService;

  final ApiService _apiService;

  Future<HyperPayResult> payWithCard({
    required int bookingId,
    required String amount,
    required String currency,
    required String paymentBrand,
  }) async {
    final checkoutId = await _apiService.createHyperPayCheckout(
      bookingId: bookingId,
      amount: amount,
      currency: currency,
      paymentBrand: paymentBrand,
    );

    if (checkoutId.isEmpty) {
      return const HyperPayResult(
        success: false,
        status: 'checkout_failed',
        message: 'Unable to create HyperPay checkout.',
      );
    }

    try {
      final result = await _channel.invokeMethod<Map>('startPayment', {
        'checkoutId': checkoutId,
        'paymentBrand': paymentBrand,
        'amount': amount,
        'currency': currency,
      });

      final status = result?['status']?.toString() ?? 'unknown';
      final transactionId = result?['transactionId']?.toString();
      final message = result?['message']?.toString();

      if (status == 'success') {
        await _apiService.createPayment(
          bookingId: bookingId,
          amount: amount,
          method: 'CARD',
          notes: 'HyperPay card payment',
        );

        return HyperPayResult(
          success: true,
          status: status,
          transactionId: transactionId,
        );
      }

      return HyperPayResult(
        success: false,
        status: status,
        transactionId: transactionId,
        message: message ?? 'Payment failed.',
      );
    } on PlatformException catch (e) {
      return HyperPayResult(
        success: false,
        status: e.code,
        message: e.message,
      );
    }
  }
}
