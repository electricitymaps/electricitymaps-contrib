//
//  DayAheadWidget.swift
//  Day Ahead Widget
//
//  Created by Mads Nedergaard on 12/09/2024.
//
import Foundation
import Intents
import SwiftUI
import WidgetKit

struct DayAheadTimelineProvider: IntentTimelineProvider {
  typealias Entry = DayAheadEntry

  //  Providing dummy data to the system to render a placeholder UI while waiting for the widget to get ready.
  func placeholder(in context: Context) -> Entry {
    // This will be masked, so actual input does not matter
    return DayAheadEntry(date: Date(), intensity: 200, zone: "DE")
  }

  // Provides data required to render the widget in the widget gallery (size/type selection page)
  func getSnapshot(
    for configuration: CustomWidgetConfIntent, in context: Context,
    completion: @escaping (Entry) -> Void
  ) {
    let entry = DayAheadEntry(date: Date(), intensity: 123, zone: "DK")
    completion(entry)
  }

  // Provides an array of timeline entries for the current time and, optionally, any future times to update a widget
  func getTimeline(
    for configuration: CustomWidgetConfIntent,
    in context: Context, completion: @escaping (Timeline<Entry>) -> Void
  ) {
    Task {
      let zone = configuration.area ?? "?"

      if zone == "?" {
        let entry = DayAheadEntry(date: Date(), intensity: nil, zone: nil)
        let timeline = Timeline(entries: [entry], policy: .never)
        completion(timeline)
      } else {

        do {
          let nextHourStart = getNextHourStart()

          let intensity = try await DataFetcher.fetchIntensity(zone: zone)
          let entry = DayAheadEntry(date: Date(), intensity: intensity, zone: zone)
          let timeline = Timeline(entries: [entry], policy: .after(nextHourStart))
          completion(timeline)
        } catch {
          print("Error fetching intensity: \(error)")
          let entry = DayAheadEntry(date: Date(), intensity: nil, zone: "?")
          let timeline = Timeline(entries: [entry], policy: .never)
          completion(timeline)
        }
      }
    }
    return
  }
}

struct DayAheadWidget: Widget {
  let kind: String = "DayAheadWidget"

  var body: some WidgetConfiguration {
    IntentConfiguration(
      kind: kind,
      intent: CustomWidgetConfIntent.self,
      provider: DayAheadTimelineProvider()
    ) {
      entry in DayAheadWidgetView(entry: entry)
    }
    .configurationDisplayName("Electricity Maps")
    .description("See the wholesale prices in your location")
    // TODO: Support other families for lock screen widgets when upgrading to ios 17
    .supportedFamilies([
      .systemSmall,
      .systemMedium
    ])
  }
}

struct DayAhead_Previews: PreviewProvider {
  static var previews: some View {
    Group {
        DayAheadWidgetView(
        entry: DayAheadEntry(
          date: Date(),
          intensity: 300,
          zone: "DE")
      )
      .previewContext(WidgetPreviewContext(family: .systemSmall))
    }
  }
}
