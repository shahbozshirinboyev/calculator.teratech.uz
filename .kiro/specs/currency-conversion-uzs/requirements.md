# Requirements Document

## Introduction

Bu hujjat calculator.teratech.uz tizimini USD valyutasidan UZS (so'm) valyutasiga o'tkazish talablarini belgilaydi. Asosiy maqsad - foydalanuvchilar uchun barcha narxlarni faqat so'm valyutasida ko'rsatish, admin panelda esa USD da narxlarni kiritish va saqlash. Tizim avtomatik ravishda USD kursini ishlatib narxlarni konvertatsiya qiladi.

## Glossary

- **System**: calculator.teratech.uz Django web ilovasi
- **Admin_Panel**: Django admin interfeysi, mahsulotlar va sozlamalarni boshqarish uchun
- **Calculator**: AIO kompyuter konfiguratsiyasini hisoblash moduli
- **Monitors**: Monitorlar katalogi va hisoblash moduli
- **Printers**: Printerlar katalogi va hisoblash moduli
- **Orders**: Buyurtmalar boshqaruv tizimi
- **USD_Rate**: Dollar kursi so'm hisobida (CalculatorSettings modelida saqlanadi)
- **User_Interface**: Foydalanuvchi ko'radigan veb-interfeys (calculator, monitors, printers, orders sahifalari)
- **Product_Price**: Mahsulot narxi USD da (admin panelda saqlanadi)
- **Display_Price**: Foydalanuvchiga ko'rsatiladigan narx so'm da
- **Order_Total**: Buyurtma umumiy summasi
- **Config_Item**: Calculator orqali yaratilgan kompyuter konfiguratsiyasi

## Requirements

### Requirement 1: Admin Panel USD Pricing

**User Story:** Admin sifatida, men mahsulotlar narxini USD da kiritishim va saqlashim kerak, shunda narx ma'lumotlari dollar valyutasida to'g'ri saqlanadi.

#### Acceptance Criteria

1. THE Admin_Panel SHALL accept Product_Price input in USD currency
2. THE Admin_Panel SHALL store all Product_Price values in USD in the database
3. THE Admin_Panel SHALL display Product_Price in USD for editing
4. THE Admin_Panel SHALL display "(USD)" currency label next to all price fields
5. WHEN an admin saves a product, THE System SHALL store the price value without currency conversion

### Requirement 2: USD Rate Management

**User Story:** Admin sifatida, men dollar kursini sozlashim kerak, shunda tizim to'g'ri konvertatsiya qiladi.

#### Acceptance Criteria

1. THE Admin_Panel SHALL provide a field to set USD_Rate in UZS (so'm)
2. THE System SHALL store USD_Rate value in CalculatorSettings model
3. WHEN USD_Rate is updated, THE System SHALL apply the new rate to all subsequent price calculations
4. THE System SHALL display USD_Rate value with "Dollar kursi (so'm)" label
5. IF USD_Rate is zero or not set, THE System SHALL use zero for conversion calculations

### Requirement 3: Calculator Display Price Conversion

**User Story:** Foydalanuvchi sifatida, men AIO calculator sahifasida barcha narxlarni faqat so'm da ko'rishim kerak, shunda men to'g'ri narx bilan tanishaman.

#### Acceptance Criteria

1. WHEN Calculator page loads, THE System SHALL fetch current USD_Rate from CalculatorSettings
2. WHEN a product is displayed, THE System SHALL convert Product_Price to Display_Price using formula: Display_Price = Product_Price × USD_Rate
3. THE User_Interface SHALL display all prices in UZS (so'm) without showing USD
4. THE User_Interface SHALL format Display_Price with thousands separator (e.g., "12 500 000")
5. THE User_Interface SHALL append "so'm" currency label to all displayed prices
6. THE Calculator SHALL calculate subtotal, markup, and total in UZS
7. THE Calculator SHALL NOT display any USD values to the user

### Requirement 4: Monitors Display Price Conversion

**User Story:** Foydalanuvchi sifatida, men Monitors sahifasida barcha narxlarni faqat so'm da ko'rishim kerak, shunda men to'g'ri narx bilan tanishaman.

#### Acceptance Criteria

1. WHEN Monitors page loads, THE System SHALL fetch current USD_Rate from CalculatorSettings
2. WHEN a monitor is displayed, THE System SHALL convert Product_Price to Display_Price using formula: Display_Price = Product_Price × USD_Rate
3. THE User_Interface SHALL display all monitor prices in UZS (so'm) without showing USD
4. THE User_Interface SHALL format Display_Price with thousands separator
5. THE User_Interface SHALL append "so'm" currency label to all displayed prices
6. THE Monitors SHALL apply markup percentage to UZS prices
7. THE Monitors SHALL NOT display any USD values to the user

### Requirement 5: Printers Display Price Conversion

**User Story:** Foydalanuvchi sifatida, men Printers sahifasida barcha narxlarni faqat so'm da ko'rishim kerak, shunda men to'g'ri narx bilan tanishaman.

#### Acceptance Criteria

1. WHEN Printers page loads, THE System SHALL fetch current USD_Rate from CalculatorSettings
2. WHEN a printer is displayed, THE System SHALL convert Product_Price to Display_Price using formula: Display_Price = Product_Price × USD_Rate
3. THE User_Interface SHALL display all printer prices in UZS (so'm) without showing USD
4. THE User_Interface SHALL format Display_Price with thousands separator
5. THE User_Interface SHALL append "so'm" currency label to all displayed prices
6. THE Printers SHALL apply markup percentage to UZS prices
7. THE Printers SHALL NOT display any USD values to the user

### Requirement 6: Orders Display in UZS

**User Story:** Foydalanuvchi va admin sifatida, men buyurtmalar ro'yxatida va tafsilotlarida narxlarni faqat so'm da ko'rishim kerak, shunda to'lov summasi aniq bo'ladi.

#### Acceptance Criteria

1. WHEN orders list page loads, THE System SHALL display Order_Total in UZS only
2. WHEN order detail page loads, THE System SHALL display all line item prices in UZS only
3. THE User_Interface SHALL format all order prices with thousands separator
4. THE User_Interface SHALL append "so'm" currency label to all order prices
5. THE Orders SHALL calculate total_price_uzs from item prices in UZS
6. THE Orders SHALL NOT display total_price_usd field to users
7. THE Orders SHALL store both USD and UZS values in database for record keeping

### Requirement 7: Order Creation with UZS Pricing

**User Story:** Sotuvchi sifatida, men buyurtma yaratganda Config_Item'larni so'm narxda ko'rishim va buyurtmani so'm summada saqlashim kerak.

#### Acceptance Criteria

1. WHEN creating an order from Calculator, THE System SHALL convert Config_Item price to UZS using current USD_Rate
2. WHEN saving an order, THE System SHALL store total_price_uzs in UZS currency
3. WHEN saving an order, THE System SHALL calculate total_price_uzs as sum of all line items in UZS
4. THE System SHALL store unit_price_usd in database for record keeping
5. THE Order form SHALL display all prices in UZS to the user
6. THE Order form SHALL display order total in UZS with "so'm" label
7. THE Order form SHALL NOT display USD prices to the user

### Requirement 8: BuildQuote Storage for Historical Reference

**User Story:** Admin sifatida, men eski konfiguratsiyalarni ko'rganimda o'sha paytdagi USD kursini va narxlarni ko'rishim kerak, shunda tarixiy ma'lumotlar saqlanadi.

#### Acceptance Criteria

1. WHEN a Config_Item is saved, THE System SHALL store USD_Rate at time of creation in BuildQuote
2. WHEN a Config_Item is saved, THE System SHALL store subtotal_price in USD in BuildQuote
3. WHEN a Config_Item is saved, THE System SHALL store total_price in USD in BuildQuote
4. WHEN a Config_Item is saved, THE System SHALL store total_price_uzs in UZS in BuildQuote
5. THE BuildQuote SHALL preserve historical pricing data even after USD_Rate changes
6. THE Admin_Panel SHALL display BuildQuote fields in both USD and UZS for audit purposes

### Requirement 9: Price Formatting and Display Consistency

**User Story:** Foydalanuvchi sifatida, men barcha sahifalarda narxlarni bir xil formatda ko'rishim kerak, shunda interfeys izchil bo'ladi.

#### Acceptance Criteria

1. THE System SHALL format all Display_Price values with space as thousands separator (e.g., "12 500 000")
2. THE System SHALL round Display_Price to nearest integer (no decimal places for UZS)
3. THE System SHALL append "so'm" text after all UZS price values
4. THE System SHALL use consistent font size and color for all price displays
5. THE System SHALL align price values consistently across all pages (Calculator, Monitors, Printers, Orders)
6. THE System SHALL NOT display fractional so'm values (no decimal places)

### Requirement 10: Markup Calculation in UZS

**User Story:** Admin sifatida, men ustama (markup) ni to'g'ri hisoblash uchun konvertatsiya tartibi muhim, shunda yakuniy narx to'g'ri bo'ladi.

#### Acceptance Criteria

1. THE System SHALL first convert Product_Price from USD to UZS using USD_Rate
2. THE System SHALL then apply markup percentage to the UZS subtotal
3. THE System SHALL apply discount percentage to the markup percentage before calculation
4. THE System SHALL calculate final price as: Subtotal_UZS × (1 + (markup% - discount%) / 100)
5. THE System SHALL use section-specific markup (aio, monitors, printers) from CalculatorSettings
6. THE System SHALL round final calculated price to nearest integer in UZS

### Requirement 11: Template Variable Conversion

**User Story:** Developer sifatida, men template'larda USD o'zgaruvchilarini UZS ga almashtirish kerak, shunda frontend to'g'ri ma'lumotlarni ko'rsatadi.

#### Acceptance Criteria

1. THE System SHALL pass Display_Price in UZS to all frontend templates
2. THE Calculator template SHALL receive total_price_uzs instead of total_price_usd
3. THE Monitors template SHALL receive monitor prices in UZS
4. THE Printers template SHALL receive printer prices in UZS
5. THE Orders templates SHALL receive order totals in UZS
6. THE Templates SHALL remove all references to USD currency labels
7. THE Templates SHALL use "so'm" currency label for all price displays

### Requirement 12: API Response Format in UZS

**User Story:** Frontend developer sifatida, men AJAX/JSON API'lardan faqat so'm da narxlarni olish kerak, shunda JavaScript to'g'ri ma'lumotlarni ko'rsatadi.

#### Acceptance Criteria

1. WHEN Calculator API returns configuration data, THE System SHALL include prices in UZS only
2. WHEN Orders API returns order data, THE System SHALL include prices in UZS only
3. THE API responses SHALL format price values as integers (no decimals)
4. THE API responses SHALL NOT include USD price fields
5. THE API responses SHALL use consistent field naming convention for UZS prices (e.g., "price_uzs", "total_uzs")

### Requirement 13: Database Migration for Existing Data

**User Story:** Admin sifatida, men mavjud ma'lumotlarni yangi tizimga ko'chirganda eski narxlar to'g'ri konvertatsiya qilinishi kerak.

#### Acceptance Criteria

1. WHEN migration runs, THE System SHALL preserve all existing USD values in database
2. WHEN migration runs, THE System SHALL recalculate total_price_uzs for all existing BuildQuote records using current USD_Rate
3. WHEN migration runs, THE System SHALL recalculate total_price_uzs for all existing Order records using current USD_Rate
4. THE System SHALL NOT delete or modify any USD price fields during migration
5. THE System SHALL log any records that fail conversion during migration

### Requirement 14: Zero or Invalid USD Rate Handling

**User Story:** Admin sifatida, men USD kursi noto'g'ri bo'lsa, tizim xatolik haqida xabar berishi kerak, shunda narxlar noto'g'ri ko'rsatilmaydi.

#### Acceptance Criteria

1. IF USD_Rate is zero, THE System SHALL display warning message "Dollar kursi sozlanmagan" to admins
2. IF USD_Rate is zero, THE User_Interface SHALL display "Narx mavjud emas" instead of zero price
3. WHEN USD_Rate is not set, THE Calculator SHALL disable price calculation functionality
4. WHEN USD_Rate is not set, THE Orders form SHALL display warning message to user
5. THE System SHALL NOT create orders when USD_Rate is zero or invalid

### Requirement 15: Admin Audit Trail for Pricing

**User Story:** Admin sifatida, men narx o'zgarishlarini kuzatish uchun tarixni ko'rishim kerak, shunda audit qilish mumkin bo'ladi.

#### Acceptance Criteria

1. THE System SHALL preserve both total_price_usd and total_price_uzs fields in Order model
2. THE System SHALL preserve both unit_price_usd in OrderItem model
3. THE System SHALL preserve USD_Rate value in BuildQuote records
4. THE Admin_Panel SHALL display both USD and UZS values in order details for audit purposes
5. THE System SHALL NOT allow modification of historical pricing data after order creation

## Implementation Notes

### Current System State
- CalculatorSettings model contains USD_Rate field
- Order model has both total_price_usd and total_price_uzs fields
- OrderItem model has unit_price_usd field
- BuildQuote model has total_price, total_price_uzs, and usd_rate fields
- Products (MonoblockBase, CPU, RAM, Storage, KeyboardMouse) store price in USD
- Monitors and Printers models store price in USD

### Key Changes Required
1. Views: Update all views to convert USD to UZS before rendering templates
2. Templates: Replace USD display with UZS display
3. Forms: Update order forms to work with UZS pricing
4. JavaScript: Update AJAX handlers to work with UZS pricing
5. Admin: Add "(USD)" labels to admin price fields

### Formula Reference
- **Display_Price (UZS)** = Product_Price (USD) × USD_Rate
- **Subtotal (UZS)** = Sum of (Product_Price × USD_Rate)
- **Final_Price (UZS)** = Subtotal_UZS × (1 + (markup% - discount%) / 100)

### Non-Functional Considerations
- Performance: USD_Rate fetched once per request using singleton pattern
- Decimal precision: Use Decimal type for all calculations
- Rounding: Round final UZS prices to integers (no decimal places)
- Database: Preserve USD values for historical data integrity
