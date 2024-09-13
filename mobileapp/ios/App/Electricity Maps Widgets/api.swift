//
//  api.swift
//  Electricity Maps Widget
//
//  Created by Mads Nedergaard on 10/11/2023.
//

import Foundation
import SwiftUI
import WidgetKit
import CryptoKit

struct APIResponse: Decodable {
  let _disclaimer: String
  let status: String
  let countryCode: String
  let data: ElectricityDetails
  let units: ElectricityUnits
}

struct ElectricityDetails: Codable {
  let datetime: String
  let carbonIntensity: Int
  let fossilFuelPercentage: Double
}

struct ElectricityUnits: Codable {
  let carbonIntensity: String
}

struct APIResponseDayAhead: Decodable {
    let data: FuturePriceData

    struct FuturePriceData: Decodable {
        let futurePrice: FuturePrice
    }

    struct FuturePrice: Decodable {
        let currency: String
        let entryCount: Int
        let priceData: [String: Float]
    }
}

struct DataFetcher {
    static func fetchDayAhead(zone: String) async throws -> [DayAheadShape] {
        // TODO: Validate zone name here?
         let url = URL(string: "https://app-backend.electricitymap.org/v8/details/hourly/\(zone)")!

        let path = "/v8/details/hourly/\(zone)"
        
        guard let apiToken = ProcessInfo.processInfo.environment["APP_BACKEND_TOKEN"] else {
            print("API Token not set")
            throw NSError(domain: "FetchErrorDomain", code: 1, userInfo: [NSLocalizedDescriptionKey: "APP_BACKEND_TOKEN is missing from environment variables."])
        }
        
        let timestamp = String(Int(Date().timeIntervalSince1970 * 1000))
        let dataToHash = "\(apiToken)\(path)\(timestamp)".utf8
        let hash = SHA256.hash(data: Data(dataToHash)).compactMap { String(format: "%02x", $0) }.joined()
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        request.addValue(timestamp, forHTTPHeaderField: "x-request-timestamp")
        request.addValue(hash, forHTTPHeaderField: "x-signature")
        
        
        let (data, response) = try await URLSession.shared.data(for: request)
        // Check and print the status code
       if let httpResponse = response as? HTTPURLResponse {
           print("Status code: \(httpResponse.statusCode)")
       } else {
           print("Failed to get HTTPURLResponse")
       }
        
        
        let result = try JSONDecoder().decode(APIResponseDayAhead.self, from: data)
        
        
        let shapes = result.data.futurePrice.priceData.compactMap { (hour, price) -> DayAheadShape? in
            if let date = iso8601Date(from: hour) {
                return DayAheadShape(hour: date, price: Double(price), currency: result.data.futurePrice.currency)
            } else {
                print("Invalid date string: \(hour)")
                return nil // Exclude invalid date entries
            }
        }
        let sortedShapes = shapes.sorted { $0.hour < $1.hour }

        return sortedShapes
    }
    static func fetchIntensity(zone: String) async throws -> Int {
        // TODO: Validate zone name here
        let url = URL(string: "https://api.co2signal.com/v1/latest?countryCode=\(zone)")!
        let (data, _) = try await URLSession.shared.data(from: url)
        let result = try JSONDecoder().decode(
            APIResponse.self, from: data)

        return Int(result.data.carbonIntensity)
    }
}
