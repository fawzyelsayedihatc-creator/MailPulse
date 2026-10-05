def inject_tracking(html_content, campaign_id, recipient_email, tracking_server_url):
    pixel_url = f"{tracking_server_url}/track/open?c={campaign_id}&e={recipient_email}"
    tracking_pixel = f'<img src="{pixel_url}" width="1" height="1" style="display:none !important;" alt="" />'
    
    if "</body>" in html_content:
        processed_html = html_content.replace("</body>", f"{tracking_pixel}</body>")
    else:
        processed_html = html_content + tracking_pixel
        
    unsub_url = f"{tracking_server_url}/track/unsubscribe?c={campaign_id}&e={recipient_email}"
    unsub_footer = f'''
    <br><hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0;" />
    <p style="font-size:12px;color:#64748b;text-align:center;">
        إذا كنت لا ترغب في استقبال هذه الإيميلات مجدداً، يمكنك <a href="{unsub_url}" style="color:#059669;">إلغاء الاشتراك من هنا</a>.
    </p>
    '''
    return processed_html + unsub_footer