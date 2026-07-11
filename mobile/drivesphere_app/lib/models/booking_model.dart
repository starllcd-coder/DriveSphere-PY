class BookingModel {
  final int id;
  final String reference;
  final String customerName;
  final String vehicleDisplay;
  final String branchName;
  final String pickupDate;
  final String returnDate;
  final String pickupLocation;
  final String returnLocation;
  final String status;
  final String currencyCode;
  final double dailyRate;
  final double depositAmount;
  final double subtotalAmount;
  final double totalAmount;
  final String createdByUsername;
  final String createdAt;
  final String updatedAt;

  BookingModel({
    required this.id,
    required this.reference,
    required this.customerName,
    required this.vehicleDisplay,
    required this.branchName,
    required this.pickupDate,
    required this.returnDate,
    required this.pickupLocation,
    required this.returnLocation,
    required this.status,
    required this.currencyCode,
    required this.dailyRate,
    required this.depositAmount,
    required this.subtotalAmount,
    required this.totalAmount,
    required this.createdByUsername,
    required this.createdAt,
    required this.updatedAt,
  });

  factory BookingModel.fromJson(Map<String, dynamic> json) {
    double parseAmount(dynamic value) {
      return double.tryParse(value.toString()) ?? 0.0;
    }

    return BookingModel(
      id: json['id'] ?? 0,
      reference: json['reference']?.toString() ?? '',
      customerName: json['customer_name']?.toString() ?? '',
      vehicleDisplay: json['vehicle_display']?.toString() ?? '',
      branchName: json['branch_name']?.toString() ?? '',
      pickupDate: json['pickup_date']?.toString() ?? '',
      returnDate: json['return_date']?.toString() ?? '',
      pickupLocation: json['pickup_location']?.toString() ?? '',
      returnLocation: json['return_location']?.toString() ?? '',
      status: json['status']?.toString() ?? '',
      currencyCode: json['currency_code']?.toString() ?? 'OMR',
      dailyRate: parseAmount(json['daily_rate']),
      depositAmount: parseAmount(json['deposit_amount']),
      subtotalAmount: parseAmount(json['subtotal_amount']),
      totalAmount: parseAmount(json['total_amount']),
      createdByUsername: json['created_by_username']?.toString() ?? '',
      createdAt: json['created_at']?.toString() ?? '',
      updatedAt: json['updated_at']?.toString() ?? '',
    );
  }
}