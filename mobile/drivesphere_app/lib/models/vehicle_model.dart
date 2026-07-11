class VehicleModel {
  final int id;
  final String brandName;
  final String modelName;
  final int year;
  final double dailyRate;
  final String status;
  final String imageUrl;
  final List<String> galleryImages;

  final String companyName;
  final String city;
  final String pickupLocation;
  final double rating;
  final double depositAmount;
  final bool companyVerified;
  final double? latitude;
  final double? longitude;

  final bool isFavorite;
  final int reviewCount;
  final String whatsappNumber;
  final bool instantBook;
  final bool deliveryAvailable;
  final bool airportPickup;
  final String engineType;
  final int minimumDriverAge;
  final int mileageLimitPerDay;
  final String insuranceCoverage;
  final String cancellationPolicy;
  final String category;
  final String transmission;
  final String fuelType;
  final int seats;
  final int luggage;

  VehicleModel({
    required this.id,
    required this.brandName,
    required this.modelName,
    required this.year,
    required this.dailyRate,
    required this.status,
    required this.imageUrl,
    this.galleryImages = const [],
    this.companyName = '',
    this.city = '',
    this.pickupLocation = '',
    this.rating = 0,
    this.depositAmount = 0,
    this.companyVerified = false,
    this.latitude,
    this.longitude,
    this.isFavorite = false,
    this.reviewCount = 0,
    this.whatsappNumber = '',
    this.instantBook = true,
    this.deliveryAvailable = false,
    this.airportPickup = false,
    this.engineType = '',
    this.minimumDriverAge = 21,
    this.mileageLimitPerDay = 250,
    this.insuranceCoverage = 'Basic included',
    this.cancellationPolicy = 'Free cancellation up to 24 hours before pickup',
    this.category = '',
    this.transmission = '',
    this.fuelType = '',
    this.seats = 0,
    this.luggage = 0,
  });

  String get fullName => '$brandName $modelName'.trim();

  bool get hasCoordinates => latitude != null && longitude != null;

  VehicleModel copyWith({
    int? id,
    String? brandName,
    String? modelName,
    int? year,
    double? dailyRate,
    String? status,
    String? imageUrl,
    List<String>? galleryImages,
    String? companyName,
    String? city,
    String? pickupLocation,
    double? rating,
    double? depositAmount,
    bool? companyVerified,
    double? latitude,
    double? longitude,
    bool? isFavorite,
    int? reviewCount,
    String? whatsappNumber,
    bool? instantBook,
    bool? deliveryAvailable,
    bool? airportPickup,
    String? engineType,
    int? minimumDriverAge,
    int? mileageLimitPerDay,
    String? insuranceCoverage,
    String? cancellationPolicy,
    String? category,
    String? transmission,
    String? fuelType,
    int? seats,
    int? luggage,
  }) {
    return VehicleModel(
      id: id ?? this.id,
      brandName: brandName ?? this.brandName,
      modelName: modelName ?? this.modelName,
      year: year ?? this.year,
      dailyRate: dailyRate ?? this.dailyRate,
      status: status ?? this.status,
      imageUrl: imageUrl ?? this.imageUrl,
      galleryImages: galleryImages ?? this.galleryImages,
      companyName: companyName ?? this.companyName,
      city: city ?? this.city,
      pickupLocation: pickupLocation ?? this.pickupLocation,
      rating: rating ?? this.rating,
      depositAmount: depositAmount ?? this.depositAmount,
      companyVerified: companyVerified ?? this.companyVerified,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      isFavorite: isFavorite ?? this.isFavorite,
      reviewCount: reviewCount ?? this.reviewCount,
      whatsappNumber: whatsappNumber ?? this.whatsappNumber,
      instantBook: instantBook ?? this.instantBook,
      deliveryAvailable: deliveryAvailable ?? this.deliveryAvailable,
      airportPickup: airportPickup ?? this.airportPickup,
      engineType: engineType ?? this.engineType,
      minimumDriverAge: minimumDriverAge ?? this.minimumDriverAge,
      mileageLimitPerDay: mileageLimitPerDay ?? this.mileageLimitPerDay,
      insuranceCoverage: insuranceCoverage ?? this.insuranceCoverage,
      cancellationPolicy: cancellationPolicy ?? this.cancellationPolicy,
      category: category ?? this.category,
      transmission: transmission ?? this.transmission,
      fuelType: fuelType ?? this.fuelType,
      seats: seats ?? this.seats,
      luggage: luggage ?? this.luggage,
    );
  }

  factory VehicleModel.fromJson(Map<String, dynamic> json) {
    double? doubleOrNull(dynamic value) {
      if (value == null) return null;
      return double.tryParse(value.toString());
    }

    final rawGallery = json['images'] ?? json['gallery'] ?? [];
    final parsedGallery = rawGallery is List
        ? rawGallery
            .map((e) => e.toString())
            .where((e) => e.isNotEmpty)
            .toList()
        : <String>[];

    return VehicleModel(
      id: json['id'] ?? 0,
      brandName:
          json['brand_name']?.toString() ?? json['brand']?.toString() ?? '',
      modelName:
          json['model_name']?.toString() ?? json['model']?.toString() ?? '',
      year: int.tryParse(json['year'].toString()) ?? 0,
      dailyRate: double.tryParse(json['daily_rate'].toString()) ?? 0.0,
      status: json['status']?.toString() ?? '',
      imageUrl: json['image_url']?.toString() ?? '',
      galleryImages: parsedGallery,
      companyName: json['company_name']?.toString() ??
          json['rental_company']?.toString() ??
          '',
      city: json['city']?.toString() ?? '',
      pickupLocation: json['pickup_location']?.toString() ??
          json['location']?.toString() ??
          '',
      rating: double.tryParse(json['rating'].toString()) ?? 0.0,
      depositAmount: double.tryParse(json['deposit_amount'].toString()) ?? 0.0,
      companyVerified: json['company_verified'] ?? false,
      latitude: doubleOrNull(json['latitude'] ?? json['lat']),
      longitude: doubleOrNull(json['longitude'] ?? json['lng']),
      isFavorite: json['is_favorite'] ?? false,
      reviewCount: int.tryParse(json['review_count'].toString()) ?? 0,
      whatsappNumber: json['whatsapp_number']?.toString() ?? '+96890000000',
      instantBook: json['instant_book'] ?? true,
      deliveryAvailable: json['delivery_available'] ?? false,
      airportPickup: json['airport_pickup'] ?? false,
      engineType: json['engine_type']?.toString() ?? '1.8L',
      minimumDriverAge:
          int.tryParse(json['minimum_driver_age'].toString()) ?? 21,
      mileageLimitPerDay:
          int.tryParse(json['mileage_limit_per_day'].toString()) ?? 250,
      insuranceCoverage:
          json['insurance_coverage']?.toString() ?? 'Basic included',
      cancellationPolicy: json['cancellation_policy']?.toString() ??
          'Free cancellation up to 24 hours before pickup',
      category: json['category']?.toString() ?? 'Sedan',
      transmission: json['transmission']?.toString() ?? 'Automatic',
      fuelType: json['fuel_type']?.toString() ?? 'Petrol',
      seats: int.tryParse(json['seats'].toString()) ?? 5,
      luggage: int.tryParse(json['luggage'].toString()) ?? 2,
    );
  }
}
