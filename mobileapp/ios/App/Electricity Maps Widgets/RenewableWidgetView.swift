//
//  RenewableWidgetView.swift
//  Electricity Maps Widget
//
//  Created by SilkeBonnen on 12/09/2024.
//

import Foundation
import SwiftUI
import UIKit
import WidgetKit

struct ViewRenewableEntry: TimelineEntry {
  let date: Date
  let renewablePercentage: Int?
  let zone: String?

  static var placeholder: ViewRenewableEntry {
    ViewRenewableEntry(

      date: Date(),
      renewablePercentage: 90,
      zone: nil
    )
  }
}


struct RenewableWidgetView: View {
    let entry: ViewRenewableEntry
    
    @Environment(\.widgetFamily) var widgetFamily

  var body: some View {
      switch widgetFamily {
          case .systemSmall:
              SmallRenewableWidgetView(entry: entry)
          case .systemMedium:
              SmallRenewableWidgetView(entry: entry)
          case .accessoryRectangular:
            LockscreenRecRenewableWidgetView(entry: entry)
        case .accessoryCircular:
          CircularRenewableWidgetView(entry: entry)
          
          default:
              Text("Unsupported widget size")
          }
    
  }
}

struct CircularRenewableWidgetView: View {
    var entry: ViewRenewableEntry
    
    var body: some View {
        if #available(iOS 17.0, *) {
            ZStack {
                Gauge(value: Double(entry.renewablePercentage ?? 0) * 0.01){
                    VStack {
                        //Text(String(entry.renewablePercentage ?? 0) + "%")
                        Text("RE")
                    }
                }
                .gaugeStyle(.accessoryCircularCapacity)

            }
            .containerBackground(for: .widget) {
                Color.black
            }
        } else {
            ZStack {
                Image("electricitymaps-icon-white")
                    .resizable()
                    .scaledToFit()
            }
            .background(Color.black)
        }
    }
}


struct LockscreenRecRenewableWidgetView: View {
    var entry: ViewRenewableEntry
    
    var body: some View {
        if entry.zone != nil {
          VStack(alignment: .center) {
              HStack {
                  Text(String(entry.renewablePercentage ?? 0) + "%")
                      .font(.system(size: 30))
                  .fontWeight(.bold)              }
                Text("Renewable")
                    .font(.system(size: 18))
                    .fontWeight(.semibold)

          }
          .padding(4)
          .padding([.horizontal], 10)
          .backgroundColor(for: entry)
          .overlay(
              RoundedRectangle(cornerRadius: 10) // Adjust the corner radius as needed
                .backgroundColor(for: entry)
                .opacity(0.35)// Set the color and width of the border
          )
        } else {
          VStack(alignment: .center) {
            Text("⚡️")
            Text("Open widget settings")
              .font(.body)
              .multilineTextAlignment(.center)

          }
            .backgroundColor(for: entry)
        }
    }
}

struct SmallRenewableWidgetView: View {
    var entry: ViewRenewableEntry
    
    var body: some View {
        if entry.zone != nil {
          VStack(alignment: .center) {

            VStack {
              Spacer()
              HStack {
                Text(String(entry.renewablePercentage ?? 0))
                  .font(.largeTitle)
                  .fontWeight(.heavy)
                  .foregroundColor(Color.white)
                Text("g")
                  .font(.system(.title))
                  .foregroundColor(Color.white)
              }
              .padding(.top)

              Text("CO₂eq/kWh")
                .font(.footnote)
                .foregroundColor(Color.white)
                .opacity(0.75)

              Spacer()
            }
            HStack {
              Text("\(formatDatee(entry.date)) · \(entry.zone ?? "?")")
                .font(.caption)
                .foregroundColor(Color(red: 0, green: 0, blue: 0, opacity: 0.4))
                .padding(.bottom, 5.0)
            }
          }

          .frame(maxWidth: .infinity, maxHeight: .infinity)
          // Custom function that allows us to support both ios17 and older
          .backgroundColor(for: entry)
        } else {
          VStack(alignment: .center) {
            Text("⚡️")
            Text("Open widget settings")
              .font(.body)
              .multilineTextAlignment(.center)

          }
        }
    }
}

@available(iOS 16.0, *)
struct View_Previews: PreviewProvider {
  static var previews: some View {
    Group {
        RenewableWidgetView(
        entry: ViewRenewableEntry(
          date: Date(),
          renewablePercentage: 70,
          zone: "DE")
      )
      .previewContext(WidgetPreviewContext(family: .accessoryRectangular))
    }
  }
}

func formatDatee(_ date: Date) -> String {
  let dateFormatter = DateFormatter()
  dateFormatter.dateFormat = "h:mm a"
  return dateFormatter.string(from: date)
}

extension View {
    @ViewBuilder
    func backgroundColor(for entry: ViewRenewableEntry) -> some View {
        if #available(iOS 17.0, *) {
            self.containerBackground(for: .widget) {
                Color.black
            }
        } else {
            self.background(Color.black)
        }
    }
}

