import React from 'react';
import { format } from 'date-fns';
import {
  X,
  Clock,
  MapPin,
  Users,
  ExternalLink,
  Repeat,
  Flag,
  Lightbulb,
  ChevronRight,
} from 'lucide-react';
import { cn } from '../../../lib/utils';
import type { CalendarEvent, Timeblock } from '@/types';

interface EventDetailsModalProps {
  isOpen: boolean;
  event: (CalendarEvent & { timeblock?: Timeblock }) | null;
  onClose: () => void;
  className?: string;
}

export const EventDetailsModal: React.FC<EventDetailsModalProps> = ({
  isOpen,
  event,
  onClose,
  className,
}) => {
  if (!event || !isOpen) return null;

  const timeblock = event.timeblock;
  const startTime = new Date(event.start);
  const endTime = new Date(event.end);
  const duration = Math.round((endTime.getTime() - startTime.getTime()) / (1000 * 60));

  // Determine accent color from event or timeblock
  const accentColor = timeblock?.courseColor || timeblock?.color || event.color || '#3b82f6';

  const isTaskEvent = timeblock?.source === 'task';

  // Extract meeting link from location
  const getMeetingInfo = () => {
    if (!timeblock?.location) return null;
    const location = timeblock.location.toLowerCase();
    
    if (location.includes('zoom.us') || location.includes('zoom.com')) {
      return { type: 'zoom', link: timeblock.location.startsWith('http') ? timeblock.location : `https://${timeblock.location}` };
    }
    if (location.includes('meet.google.com')) {
      return { type: 'meet', link: timeblock.location.startsWith('http') ? timeblock.location : `https://${timeblock.location}` };
    }
    if (location.includes('teams.microsoft.com') || location.includes('teams.live.com')) {
      return { type: 'teams', link: timeblock.location.startsWith('http') ? timeblock.location : `https://${timeblock.location}` };
    }
    return null;
  };

  const meetingInfo = getMeetingInfo();

  return (
    <div
      className={`fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 transition-all duration-300 ${
        isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
      }`}
      onClick={onClose} // Click backdrop to close
    >
      <div
        className={cn(
          `border border-gray-700/50 w-full max-w-lg rounded-2xl max-h-[80vh] flex flex-col overflow-hidden transition-all duration-300 ${
            isOpen ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
          }`,
          className
        )}
        style={{ backgroundColor: '#181818' }}
        onClick={(e) => e.stopPropagation()} // Prevent closing when clicking modal content
      >
        {isOpen ? (
          <>
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
                <div className="flex-1 min-w-0">
                <p className="text-xs text-white tracking-wide mb-1">Event</p>
                  <h2 className="text-lg font-semibold text-white truncate">{event.title}</h2>
                  {timeblock?.courseName && (
                  <p className="text-sm text-gray-400 truncate mt-0.5">{timeblock.courseName}</p>
                  )}
              </div>
              <button
                onClick={onClose}
                className="p-1.5 hover:bg-white/5 rounded-lg transition-colors shrink-0 ml-2"
              >
                <X className="w-4 h-4 text-gray-500 hover:text-white" />
              </button>
            </div>

            {/* Content */}
            <div className="px-6 py-4 overflow-y-auto flex-1 space-y-4">
              {/* Time Section */}
              <div className="space-y-2">
                    {event.allDay ? (
                      <div>
                    <p className="text-sm text-white font-medium">All day</p>
                    <p className="text-sm text-white mt-0.5">{format(startTime, 'EEE MMM d')}</p>
                      </div>
                    ) : (
                  <div className="flex items-center gap-2">
                    <Clock size={16} className="text-gray-500" />
                    <div className="flex items-center gap-1">
                      <p className="text-sm text-white">{format(startTime, 'h:mm a')}</p>
                      <ChevronRight size={14} className="text-gray-500" />
                      <p className="text-sm text-white">{format(endTime, 'h:mm a')}</p>
                      </div>
                    <p className="text-xs text-gray-500 ml-2">{duration} min</p>
                  </div>
                )}
                <p className="text-sm text-white pl-6">{format(startTime, 'EEE MMM d')}</p>

                {/* Recurrence & Location */}
                {timeblock?.recurrence && (
                  <div className="flex items-center gap-2 text-xs">
                    <Repeat size={14} className="text-gray-500" />
                    <span className="text-gray-400">Every week on Mon, Wed...</span>
                  </div>
                )}
                {timeblock?.location && !meetingInfo && (
                  <div className="flex items-center gap-2 text-xs">
                    <MapPin size={14} className="text-gray-500" />
                    <span className="text-gray-400 truncate">{timeblock.location}</span>
                  </div>
                )}
              </div>

              {/* Participants Section */}
              {timeblock?.attendees && timeblock.attendees.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Users size={16} className="text-gray-500" />
                    <span className="text-xs text-gray-400">{timeblock.attendees.length} participants</span>
                  </div>

                  <div className="space-y-3">
                    {timeblock.attendees.slice(0, 5).map((attendee, idx) => {
                      const displayName = attendee.name || attendee.email || 'Unknown';
                      const email = attendee.email;
                      const responseStatus = attendee.responseStatus;

                      const initials = displayName.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
                      const isOrganizer = email && timeblock.organizer?.email === email;

                      return (
                        <div key={idx} className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full bg-neutral-700 flex items-center justify-center text-xs text-white shrink-0">
                            {initials}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-white truncate">{displayName}</p>
                              {email && email !== displayName && (
                              <p className="text-xs text-gray-500 truncate">{email}</p>
                              )}
                            {responseStatus && (
                              <p className="text-xs text-gray-500 capitalize">
                                {responseStatus.replace('_', ' ')}
                              </p>
                            )}
                          </div>
                          {isOrganizer && (
                            <span className="text-xs text-gray-500 shrink-0">Organizer</span>
                          )}
                        </div>
                      );
                    })}
                    {timeblock.attendees.length > 5 && (
                      <button className="text-xs text-gray-400 hover:text-white transition-colors">
                        See all {timeblock.attendees.length} participants
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Meeting Link Section */}
              {meetingInfo && timeblock && (
                <div className="space-y-3">
                  <a
                    href={meetingInfo.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg font-medium text-white text-sm transition-all hover:opacity-90"
                    style={{
                      backgroundColor: meetingInfo.type === 'meet' ? '#00832d' : 
                                     meetingInfo.type === 'zoom' ? '#2d8cff' : 
                                     meetingInfo.type === 'teams' ? '#6264a7' : accentColor
                    }}
                  >
                    {meetingInfo.type === 'meet' && 'Join Google Meet'}
                    {meetingInfo.type === 'zoom' && 'Join Zoom Meeting'}
                    {meetingInfo.type === 'teams' && 'Join Teams Meeting'}
                  </a>
                  {timeblock.location && (
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      <ExternalLink size={14} className="text-gray-500" />
                      <span>{timeblock.location.split('/').pop() || timeblock.location}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Description */}
              {timeblock?.description && (
                <div>
                  <p className="text-sm text-white whitespace-pre-wrap">{timeblock.description}</p>
                </div>
              )}

              {/* Task-specific metadata */}
              {isTaskEvent && (
                <div className="space-y-2">
                    {timeblock?.priority && (
                      <div className="flex items-center gap-2">
                      <Flag size={14} className="text-gray-500" />
                      <span className="text-xs text-gray-400">{timeblock.priority} priority</span>
                      </div>
                    )}
                  {timeblock?.estimatedMinutes && (
                    <div className="flex items-center gap-2">
                      <Clock size={14} className="text-gray-500" />
                      <span className="text-xs text-gray-400">Estimated {timeblock.estimatedMinutes} minutes</span>
                    </div>
                  )}
                  {timeblock?.schedulingRationale && (
                    <div className="flex items-start gap-2 pt-1">
                      <Lightbulb size={14} className="text-gray-500 shrink-0 mt-0.5" />
                      <p className="text-xs text-gray-400 leading-relaxed">{timeblock.schedulingRationale}</p>
                    </div>
                  )}
                  {timeblock?.tags && timeblock.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 pt-1">
                        {timeblock.tags.map((tag, idx) => (
                          <span
                            key={idx}
                          className="px-2 py-1 bg-neutral-700 text-white text-xs rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
              )}
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
};

EventDetailsModal.displayName = 'EventDetailsModal';
