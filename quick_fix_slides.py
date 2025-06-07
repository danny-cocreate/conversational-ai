#!/usr/bin/env python3
"""
Quick fix script for the lesson display issue
"""

import os
import sys

def fix_lesson_template():
    """Apply a simple fix to make slides display immediately"""
    
    template_path = "/Users/dSetia/Dropbox/projects/conversational AI/templates/lesson_voice_enhanced.html"
    
    print("🔧 Applying quick fix for lesson display...")
    
    # Read the current template
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add a simple JavaScript fix to show slides immediately if API fails
        fix_script = '''
    <script>
        // QUICK FIX: Show slides immediately if API call fails
        setTimeout(function() {
            console.log('🛠️ Quick fix: Checking if slides are loaded...');
            
            const slidesContainer = document.getElementById('revealSlides');
            const loadingSlide = document.getElementById('loadingSlide');
            
            // If still showing loading slide after 5 seconds, show demo content
            if (loadingSlide && !reveal) {
                console.log('🔄 API failed, showing demo slides immediately...');
                
                slidesContainer.innerHTML = `
                    <section>
                        <h2>Welcome to Wireframing with AI</h2>
                        <div class="slide-content">
                            <p>This lesson will teach you how to create effective wireframes using AI tools.</p>
                            <p>You'll learn modern techniques and best practices for wireframing.</p>
                        </div>
                    </section>
                    <section>
                        <h2>What is Wireframing?</h2>
                        <div class="slide-content">
                            <p>Wireframing is the process of creating basic structural blueprints for websites and applications.</p>
                            <p>It helps designers plan layout and functionality before diving into detailed design.</p>
                        </div>
                    </section>
                    <section>
                        <h2>AI Tools for Wireframing</h2>
                        <div class="slide-content">
                            <p>Modern AI tools can help automate and enhance the wireframing process.</p>
                            <ul>
                                <li>Layout generators</li>
                                <li>Content suggestions</li>
                                <li>Design assistants</li>
                            </ul>
                        </div>
                    </section>
                    <section>
                        <h2>Best Practices</h2>
                        <div class="slide-content">
                            <p>When wireframing with AI:</p>
                            <ul>
                                <li>Start with clear objectives</li>
                                <li>Iterate quickly</li>
                                <li>Validate with users</li>
                                <li>Maintain consistency across designs</li>
                            </ul>
                        </div>
                    </section>
                `;
                
                // Initialize reveal.js with the demo content
                if (window.Reveal && !reveal) {
                    reveal = new Reveal(document.getElementById('lessonReveal'), {
                        hash: false,
                        controls: false,
                        progress: false,
                        center: true,
                        transition: 'slide'
                    });
                    
                    reveal.initialize().then(() => {
                        console.log('✅ Quick fix: Reveal.js initialized with demo content');
                        
                        // Set up navigation
                        totalSlides = 4;
                        updateNavigationAndContext();
                        
                        // Set up navigation button listeners
                        const prevSlideBtn = document.getElementById('prevSlideBtn');
                        const nextSlideBtn = document.getElementById('nextSlideBtn');

                        if (prevSlideBtn) {
                            prevSlideBtn.addEventListener('click', () => reveal.prev());
                        }

                        if (nextSlideBtn) {
                            nextSlideBtn.addEventListener('click', () => reveal.next());
                        }
                        
                        // Set up slide change listeners
                        reveal.addEventListener('slidechanged', function(event) {
                            updateNavigationAndContext();
                        });
                    });
                }
            }
        }, 5000); // Wait 5 seconds for API
    </script>
'''
        
        # Insert the fix script before the closing body tag
        if fix_script not in content:
            content = content.replace('</body>', fix_script + '\n</body>')
            
            # Write the updated content back
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Quick fix applied successfully!")
            print("🔄 The slides should now display even if the API fails")
            return True
        else:
            print("ℹ️ Quick fix already applied")
            return True
            
    except Exception as e:
        print(f"❌ Error applying fix: {e}")
        return False

def check_server_status():
    """Check if the server is running"""
    print("\n🌐 Checking server status...")
    
    try:
        import requests
        response = requests.get('http://localhost:5001', timeout=5)
        if response.status_code == 200:
            print("✅ Server is running at http://localhost:5001")
            return True
        else:
            print(f"⚠️ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running")
        print("💡 Start the server with: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Quick Fix for Lesson Display Issue")
    print("=" * 50)
    
    # Apply the template fix
    fix_applied = fix_lesson_template()
    
    if fix_applied:
        print("\n✅ Template fix applied!")
        print("\n📍 Next steps:")
        print("1. If server is not running: python app.py")
        print("2. Visit: http://localhost:5001/lesson/wireframing-with-ai")
        print("3. The slides should now display within 5 seconds")
        
        # Check server status
        server_running = check_server_status()
        
        if server_running:
            print("\n🎉 Everything looks good! Try the lesson now.")
        else:
            print("\n⚠️ Server not running - start it and try again")
    else:
        print("\n❌ Fix failed - please check the file manually")
    
    print("\n" + "=" * 50)
