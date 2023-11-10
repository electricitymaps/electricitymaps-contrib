//
//  View.swift
//  Electricity Maps Widget
//
//  Created by Mads Nedergaard on 10/11/2023.
//

// XCode15 only
//#Preview {
//    ViewSizeWidgetView(entry)
//}
import Foundation
import UIKit
import WidgetKit
import SwiftUI


struct ViewSizeEntry: TimelineEntry {
    let date: Date
    let intensity: Int?
    let zone: String?
    
    
    static var placeholder: ViewSizeEntry {
        ViewSizeEntry(
            
            date: Date(),
            intensity: 123,
            zone: nil
        )
    }
}


struct ViewSizeWidgetView : View {
    let entry: ViewSizeEntry
    
    var body: some View {
        
        if (entry.zone != nil) {
            VStack(alignment: .center) {
                
                VStack {
                    Spacer()
                    HStack {
                        Text(String(entry.intensity ?? 0))
                            .font(.largeTitle)
                            .fontWeight(.heavy)
                            .foregroundColor(getTextColor(intensity: entry.intensity, type: "main"))
                        Text("g")
                            .font(.system(.title))
                            .foregroundColor(getTextColor(intensity: entry.intensity, type: "main"))
                    }
                    .padding(.top)
                    
                    Text("CO₂eq/kWh")
                        .font(.footnote)
                        .foregroundColor(getTextColor(intensity: entry.intensity, type: "subtitle"))
                        .opacity(0.75)
                    
                    Spacer()
                }
                HStack {
                    Text("\(formatDate(entry.date)) · \(entry.zone ?? "?")")
                        .font(.caption)
                        .foregroundColor(Color(red: 0, green: 0, blue: 0, opacity: 0.4))
                        .padding(.bottom, 5.0)
                }
                
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color(getBackgroundColor(intensity: entry.intensity)))
        } else {
            VStack(alignment: .center) {
                Text("⚡️")
                Text("Open widget settings")
                    .font(.body)
                    .multilineTextAlignment(.center)
                
            }
        }
        
        
        // TODO: Widget deep link?
        //.widgetURL(WidgetDeepLink.yourDeepLinkURL(entry: entry))
        
        // ios 17 only
        //.containerBackground(for: .widget) {
        //    Color.green
        //}
        
    }
    func formatDate(_ date: Date) -> String {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "h:mm a"
        return dateFormatter.string(from: date)
    }
    

}

struct View_Previews: PreviewProvider {
    static var previews: some View {
                Group {
                    ViewSizeWidgetView(entry: ViewSizeEntry(
                        date: Date(),
                        intensity: 300,
                        zone: "DK-DK2")
                    )
                        .previewContext(WidgetPreviewContext(family: .systemSmall))
                }
    }
}
