class NotificationModel {
  final int id;
  final String title;
  final String message;
  final String notificationType;
  final bool isRead;
  final String createdAt;

  NotificationModel({
    required this.id,
    required this.title,
    required this.message,
    required this.notificationType,
    required this.isRead,
    required this.createdAt,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      id: json['id'] ?? 0,
      title: json['title']?.toString() ?? '',
      message: json['message']?.toString() ?? '',
      notificationType: json['notification_type']?.toString() ?? '',
      isRead: json['is_read'] ?? false,
      createdAt: json['created_at']?.toString() ?? '',
    );
  }
}