class PaymentModel {
  final int id;
  final String receiptNumber;
  final int bookingId;
  final String bookingReference;
  final String customerName;
  final String vehicleDisplay;
  final String branchName;
  final String paymentDate;
  final String method;
  final double amount;
  final String currencyCode;
  final String status;
  final String notes;
  final String createdByEmail;
  final String createdAt;
  final String updatedAt;

  PaymentModel({
    required this.id,
    required this.receiptNumber,
    required this.bookingId,
    required this.bookingReference,
    required this.customerName,
    required this.vehicleDisplay,
    required this.branchName,
    required this.paymentDate,
    required this.method,
    required this.amount,
    required this.currencyCode,
    required this.status,
    required this.notes,
    required this.createdByEmail,
    required this.createdAt,
    required this.updatedAt,
  });

  factory PaymentModel.fromJson(Map<String, dynamic> json) {
    double parseAmount(dynamic value) {
      return double.tryParse(value.toString()) ?? 0.0;
    }

    return PaymentModel(
      id: json['id'] ?? 0,
      receiptNumber: json['receipt_number']?.toString() ?? '',
      bookingId: json['booking_id'] ?? 0,
      bookingReference: json['booking_reference']?.toString() ?? '',
      customerName: json['customer_name']?.toString() ?? '',
      vehicleDisplay: json['vehicle_display']?.toString() ?? '',
      branchName: json['branch_name']?.toString() ?? '',
      paymentDate: json['payment_date']?.toString() ?? '',
      method: json['method']?.toString() ?? '',
      amount: parseAmount(json['amount']),
      currencyCode: json['currency_code']?.toString() ?? 'OMR',
      status: json['status']?.toString() ?? '',
      notes: json['notes']?.toString() ?? '',
      createdByEmail: json['created_by_email']?.toString() ?? '',
      createdAt: json['created_at']?.toString() ?? '',
      updatedAt: json['updated_at']?.toString() ?? '',
    );
  }
}