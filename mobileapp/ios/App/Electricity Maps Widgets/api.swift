//
//  api.swift
//  Electricity Maps Widget
//
//  Created by Mads Nedergaard on 10/11/2023.
//

import Foundation
import SwiftUI
import WidgetKit

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

    static func fetchDayAhead(zone: String) async throws -> Int {
        // TODO: Make this work with the actual backend with authentication
        let url = URL(string: "http://localhost:8001/v8/details/hourly/\(zone)")!
        // let url = URL(string: "https://app-backend.electricitymap.org/v8/details/hourly/\(zone)")!
        // let path = ...
        // let token = ...
        // let timestamp = String(Date().timeIntervalSince1970)
        // url.addValue("x-request-timestamp", forHTTPHeaderField: timestamp)
        // url.addValue("x-signature", forHTTPHeaderField: getHeaders(path: "/v8/details/hourly/\(zone)", timestamp: timestamp, token: token))
        let (data, _) = try await URLSession.shared.data(from: url)
        let result = try JSONDecoder().decode(APIResponseDayAhead.self, from: data)

        // TODO: Return the full list in an appropriate format for the view to show
        return Int(result.data.futurePrice.entryCount)
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
