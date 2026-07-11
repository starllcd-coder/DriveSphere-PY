class SupportMessageModel {
  final int id;
  final String message;
  final String sender;
  final String createdAt;

  const SupportMessageModel({
    required this.id,
    required this.message,
    required this.sender,
    required this.createdAt,
  });

  factory SupportMessageModel.fromJson(Map<String, dynamic> json) {
    return SupportMessageModel(
      id: json['id'] ?? 0,
      message: json['message']?.toString() ?? '',
      sender: json['sender']?.toString() ?? 'customer',
      createdAt: json['created_at']?.toString() ?? '',
    );
  }
}
