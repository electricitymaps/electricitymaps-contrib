//
//  colors.swift
//  Electricity Maps Widget
//
//  Created by Mads Nedergaard on 10/11/2023.
//

import UIKit

import WidgetKit
import SwiftUI

public func getTextColor(intensity: Int?, type: String) -> Color {
    guard let unwrappedIntensity = intensity else {
        // Handle the case where the value is nil
        print("The value is nil.")
        return .white
    }
    
    if (type == "main") {
        if (unwrappedIntensity > 80 && unwrappedIntensity < 250) {
            return .black
        } else {
            return .white
        }
    }
    if (unwrappedIntensity < 600) {
        return .black
    } else {
        return .white
    }
    
}

public func getBackgroundColor(intensity: Int?) -> UIColor {
    guard let unwrappedValue = intensity else {
        // Handle the case where the value is nil
        print("The value is nil.")
        return UIColor.black
    }
    
    let scale = [0, 150, 600, 800, 1100, 1500]
    let colors: [UIColor] = [
        UIColor(red: 42/255, green: 163/255, blue: 100/255, alpha: 1.0),    // #2AA364
        UIColor(red: 245/255, green: 235/255, blue: 77/255, alpha: 1.0),    // #F5EB4D
        UIColor(red: 158/255, green: 66/255, blue: 41/255, alpha: 1.0),     // #9E4229
        UIColor(red: 56/255, green: 29/255, blue: 2/255, alpha: 1.0),       // #381D02
        UIColor(red: 56/255, green: 29/255, blue: 2/255, alpha: 1.0),       // #381D02
        UIColor.black
    ]
    
    let normalizedValue = min(max(Double(unwrappedValue), Double(scale.first!)), Double(scale.last!))
    
    // Find the two closest colors in the scale
    var startIndex = 0
    while startIndex < scale.count - 1 && normalizedValue > Double(scale[startIndex + 1]) {
        startIndex += 1
    }
    
    let endIndex = min(startIndex + 1, scale.count - 1)
    
    // Interpolate between the two colors based on the normalized value
    let t = (normalizedValue - Double(scale[startIndex])) / (Double(scale[endIndex]) - Double(scale[startIndex]))
    let startColor = colors[startIndex]
    let endColor = colors[endIndex]
    
    let interpolatedColor = UIColor.interpolate(from: startColor, to: endColor, with: CGFloat(t))
    
    return interpolatedColor
}


extension UIColor {
    static func interpolate(from: UIColor, to: UIColor, with t: CGFloat) -> UIColor {
        var fromRed: CGFloat = 0.0, fromGreen: CGFloat = 0.0, fromBlue: CGFloat = 0.0, fromAlpha: CGFloat = 0.0
        var toRed: CGFloat = 0.0, toGreen: CGFloat = 0.0, toBlue: CGFloat = 0.0, toAlpha: CGFloat = 0.0
        
        from.getRed(&fromRed, green: &fromGreen, blue: &fromBlue, alpha: &fromAlpha)
        to.getRed(&toRed, green: &toGreen, blue: &toBlue, alpha: &toAlpha)
        
        let interpolatedRed = fromRed + (toRed - fromRed) * t
        let interpolatedGreen = fromGreen + (toGreen - fromGreen) * t
        let interpolatedBlue = fromBlue + (toBlue - fromBlue) * t
        let interpolatedAlpha = fromAlpha + (toAlpha - fromAlpha) * t
        
        return UIColor(red: interpolatedRed, green: interpolatedGreen, blue: interpolatedBlue, alpha: interpolatedAlpha)
    }
}
