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

struct DataFetcher {
  static func fetchIntensity(zone: String) async throws -> Int {
    // TODO: Validate zone name here
    let url = URL(string: "https://api.co2signal.com/v1/latest?countryCode=\(zone)")!
    let (data, _) = try await URLSession.shared.data(from: url)
    let result = try JSONDecoder().decode(
      APIResponse.self, from: data)

    return Int(result.data.carbonIntensity)
  }
}
